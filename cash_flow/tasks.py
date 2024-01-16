from datetime import datetime, timedelta
from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.db.models import Q, Sum, When, Case, F
from cash_flow.external_calls import (get_due_amount_response, get_collection_poll_response, get_nbfc_list,
                                      get_collection_amount_response, get_loan_booked_data, get_failed_loan_data)
from cash_flow.models import (NbfcWiseCollectionData, ProjectionCollectionData, NbfcBranchMaster,
                              CollectionAndLoanBookedData, CollectionLogs, LoanDetail, LoanBookedLogs)
from utils.common_helper import Common
from cash_flow_prediction.celery import celery_error_email


@shared_task()
@celery_error_email
def populate_json_against_nbfc():
    """
    celery task to populate the models.NbfcWiseCollectionData
    """
    collection_poll_data = get_collection_poll_response().json()
    if collection_poll_data:
        nbfc_dict = collection_poll_data.get("data", {})

        for nbfc_id, json in nbfc_dict.items():
            try:
                nbfc_instance = NbfcBranchMaster.objects.get(id=nbfc_id)
            except ObjectDoesNotExist:
                continue
            nbfc_wise_collection_instance = NbfcWiseCollectionData(
                nbfc=nbfc_instance,
                collection_json=json
            )
            nbfc_wise_collection_instance.save()


@shared_task()
@celery_error_email
def populate_wacm():
    """
    celery task to populate the models.ProjectionCollectionData
    """
    current_date = datetime.now()
    due_date = (current_date + relativedelta(months=1)) - timedelta(1)
    formatted_due_date = due_date.strftime('%Y-%m-%d')
    dd_str = str(due_date.day)
    projection_response_data = get_due_amount_response(formatted_due_date).json()
    if projection_response_data:
        projection_response_data = projection_response_data.get('data', {})
    nbfc_list = list(projection_response_data.keys())
    nbfc_ids = NbfcBranchMaster.objects.filter(id__in=nbfc_list).order_by('created_at')
    nbfc_ids = dict(nbfc_ids.values_list('branch_name', 'id'))
    nbfc_ids_list = list(nbfc_ids.values())
    queryset = NbfcWiseCollectionData.objects.filter(nbfc_id__in=nbfc_ids_list).order_by('created_at')
    queryset = dict((str(nbfc_id), collection_json) for nbfc_id, collection_json in
                    queryset.values_list('nbfc_id', 'collection_json'))

    for nbfc_id, projection_amount in projection_response_data.items():
        collection_json = {}
        if nbfc_id in queryset:
            collection_json = queryset[nbfc_id]

        ce_new_json = collection_json.get(dd_str, {}).get("New", {})
        ce_old_json = collection_json.get(dd_str, {}).get("Old", {})
        wace_dict = Common.get_wace_against_due_date(ce_new_json, ce_old_json)

        for dpd_date in wace_dict.keys():
            dpd_date_str = str(dpd_date)
            collection_date = due_date + timedelta(int(dpd_date))

            try:
                nbfc_instance = NbfcBranchMaster.objects.get(id=nbfc_id)
            except ObjectDoesNotExist:
                continue

            # db constraint of not getting the duplicate set of same nbfc, due_date and collection_date
            obj, created = ProjectionCollectionData.objects.get_or_create(
                nbfc=nbfc_instance,
                due_date=due_date,
                collection_date=collection_date,
                defaults={'amount': wace_dict[dpd_date_str] * projection_amount}
            )

            # If the object already existed, update its amount field
            if not created:
                obj.amount = wace_dict[dpd_date_str] * projection_amount
                obj.save()


@shared_task()
@celery_error_email
def populate_nbfc_branch_master():
    """
    celery task to populate nbfc branch master storing nbfc's with the corresponding id's
    """
    nbfc_list_data_response = get_nbfc_list().json()
    if nbfc_list_data_response:

        for entry in nbfc_list_data_response['data']:
            branch_id = entry.get('id', None)
            branch_name = entry.get('branch_name', None)
            delay_in_disbursal = entry.get('delay_in_disbursal', None)

            if branch_id and branch_name:
                master_instance = NbfcBranchMaster.objects.filter(id=branch_id, branch_name=branch_name).first()

                if master_instance:
                    master_instance.delay_in_disbursal = delay_in_disbursal
                else:
                    master_instance = NbfcBranchMaster(id=branch_id, branch_name=branch_name,
                                                       delay_in_disbursal=delay_in_disbursal)
                master_instance.save()


@shared_task()
@celery_error_email
def populate_collection_amount():
    """
    celery task to populate the collection amount in models.CollectionAndLoanBookedData
    for a nbfc's for a particular due_date
    the celery task would also log the changes into the models.CollectionLogs for every change pre
    celery task and post celery task collection amount
    """
    due_date = datetime.now()
    str_due_date = due_date.strftime('%Y-%m-%d')
    collection_amount_response = get_collection_amount_response(str_due_date).json()
    if collection_amount_response:
        collection_amount_data = collection_amount_response.get('data', {})
        for nbfc_id, collection_amount in collection_amount_data.items():
            try:
                nbfc_instance = NbfcBranchMaster.objects.get(id=nbfc_id)
            except ObjectDoesNotExist:
                continue

            # Try to get an existing record for the NBFC and due_date
            collection_instance, created = CollectionAndLoanBookedData.objects.get_or_create(
                nbfc=nbfc_instance,
                due_date=due_date,
                defaults={'collection': collection_amount}
            )

            # If the record already existed, update its collection field
            if not created:
                collection_instance.collection = collection_amount
                # calculating the pre save amount of collection present in the db
                pre_saved_collection_amount = 0
                pre_saved_collection_instance = CollectionAndLoanBookedData.objects.filter(
                    nbfc=nbfc_instance,
                    due_date=due_date
                ).first()
                if pre_saved_collection_instance:
                    pre_saved_collection_amount = pre_saved_collection_instance.collection
                if collection_amount is None:
                    collection_amount = 0
                amount_diff = collection_amount - pre_saved_collection_amount
                # saving the collection log too
                collection_log_instance = CollectionLogs(
                    collection=collection_instance,
                    amount=amount_diff
                )
                collection_log_instance.save()
                collection_instance.save()
            else:
                # case of having the first log of this particular nbfc and due_date
                collection_log_instance = CollectionLogs(
                    collection=collection_instance,
                    amount=collection_amount
                )
                collection_log_instance.save()


@shared_task()
@celery_error_email
def populate_loan_booked_amount():
    """
    celery task to populate the loan_booked amount in models.CCollectionAndLoanBookedData
    for a nbfc's for a particular due_date
    """
    due_date = datetime.now()
    str_due_date = due_date.strftime('%Y-%m-%d')
    loan_booked_response = get_loan_booked_data(str_due_date).json()
    if loan_booked_response:
        loan_booked_data = loan_booked_response.get('data', {})
        for nbfc_id, loan_booked in loan_booked_data.items():
            try:
                nbfc_instance = NbfcBranchMaster.objects.get(id=nbfc_id)
            except ObjectDoesNotExist:
                continue

            # Try to get an existing record for the NBFC and due_date
            loan_booked_instance, created = CollectionAndLoanBookedData.objects.get_or_create(
                nbfc=nbfc_instance,
                due_date=due_date,
                defaults={'loan_booked': loan_booked}
            )

            # If the record already existed, update its loan_booked field
            if not created:
                loan_booked_instance.loan_booked = loan_booked
                loan_booked_instance.save()


@shared_task()
@celery_error_email
def unbook_failed_loans():
    """
    this celery function will get the data for the failed loans and unbook the loans in models.LoanDetail
    """
    failed_loans_data = get_failed_loan_data().json()
    if failed_loans_data:
        failed_loans_list = failed_loans_data.get('data', None)
        if failed_loans_list:
            loans = LoanDetail.objects.filter(loan_id__in=failed_loans_list, status='P')
            for loan in loans.iterator(chunk_size=500):
                loan.status = 'F'
                unbooked_amount = loan.amount
                loan_log_instance = LoanBookedLogs(
                    loan=loan,
                    amount=unbooked_amount,
                    request_type='LF',
                    log_text='Unbooking the amount due to loan failure'
                )
                nbfc_id = loan.nbfc
                user_type = loan.user_type
                available_balance = cache.get('available_balance', {})
                available_balance[nbfc_id][user_type] += unbooked_amount
                available_balance[nbfc_id]['total'] += unbooked_amount
                cache.set('available_balance', available_balance)
                loan_log_instance.save()


@shared_task()
@celery_error_email
def populate_available_cash_flow(nbfc=None):
    """
    celery task to store json of nbfc id against available cash flow in the cache by repeated calculation
    """
    filtered_dict = {}
    if nbfc:
        filtered_dict['nbfc_id'] = nbfc

    due_date = datetime.now().date()
    hold_cash_value = Common.get_hold_cash_value(due_date)
    capital_inflow_value = Common.get_nbfc_capital_inflow(due_date)

    prediction_amount_value = dict(ProjectionCollectionData.objects.filter(
        **filtered_dict,
        collection_date=due_date).values('nbfc_id').order_by('nbfc_id').annotate(
        total_amount=Sum('amount')
    ).values_list('nbfc_id', 'total_amount'))

    user_ratio_value = Common.get_user_ratio(due_date)

    collection_value = dict((CollectionAndLoanBookedData.objects.filter(due_date=due_date, **filtered_dict).
                             values_list('nbfc_id', 'last_day_balance')))

    cal_data = {}
    for nbfc_id in collection_value:
        hold_cash = hold_cash_value.get(nbfc_id, 0)
        if hold_cash == 100:
            continue
        prediction_cash_inflow = prediction_amount_value.get(nbfc_id, 0)
        prev_day_carry_forward = collection_value.get(nbfc_id, 0)

        capital_inflow = capital_inflow_value.get(nbfc_id, 0)

        available_cash_flow = Common.get_available_cash_flow(prediction_cash_inflow, prev_day_carry_forward,
                                                             capital_inflow, hold_cash)

        user_ratio = user_ratio_value.get(nbfc_id, [100, 0])
        old_ratio = user_ratio[0]
        new_ratio = user_ratio[1]

        old_value = (available_cash_flow * old_ratio) / 100
        new_value = (available_cash_flow * new_ratio) / 100

        cal_data[nbfc_id] = {
            'O': old_value,
            'N': new_value,
            'total': available_cash_flow
        }

    if nbfc:
        return cal_data.get(nbfc, {}).get('total', 0)
    cache.set('available_balance', cal_data)


@shared_task()
@celery_error_email
def task_for_loan_booked(nbfc_id=None):
    """
    celery task for loan booked
    :return:
    """
    filtered_dict = {}
    if nbfc_id:
        filtered_dict['nbfc_id'] = nbfc_id

    due_date = datetime.now().date()
    loan_booked_instance = LoanDetail.objects.filter(created_at__date=due_date, is_booked=True,
                                                     **filtered_dict).exclude(status='F')
    loan_booked_instance = loan_booked_instance.annotate(
        value=Case(
            When(status='P', then=F('amount')),
            default=F('credit_limit')
        )
    )
    loan_booked_instance = loan_booked_instance.values('nbfc_id').order_by('nbfc_id').annotate(
        total_amount=Sum('value')
    )
    loan_booked = dict(loan_booked_instance.values_list('nbfc_id', 'total_amount'))
    if nbfc_id:
        return loan_booked.get(nbfc_id, 0)

    cache.set('loan_booked', loan_booked)


@shared_task()
@celery_error_email
def task_for_loan_booking(credit_limit, loan_type, request_type, user_id, user_type, cibil_score,
                          nbfc_id, loan_amount=None,
                          loan_id=None):
    """
    helper function to book the loan with logging in models.LoanBookedLogs
    we have to book the loans at the loan application level and loan applied status
    if at the loan application status loan_status will be 'I' and the is booked will be true and request
    type will be 'LAN' and the amount applied by the user will be booked but first checking the loan instance if
    present or not from the credit limit request type
    :param credit_limit: int value for credit limit assigned to the user
    :param loan_type:
    :param request_type:
    :param user_id:
    :param user_type:
    :param cibil_score:
    :param loan_amount:
    :param nbfc_id: nbfc to be booked in the loan detail
    :param loan_id:
    :return:
    """
    due_date = datetime.now().date()
    user_loan = LoanDetail.objects.filter(user_id=user_id, created_at__date=due_date).first()
    loan_detail_id = None
    if user_loan:
        loan_detail_id = user_loan.id
    diff_amount = 0
    booked_amount = 0
    if request_type == 'LAN':
        loan_data = {
            'nbfc_id': nbfc_id,
            'user_id': user_id,
            'cibil_score': cibil_score,
            'credit_limit': credit_limit,
            'loan_type': loan_type,
            'user_type': user_type,
            'is_booked': True,
            'status': 'I'
        }
        loan_log = {
            'amount': credit_limit,
            'log_text': 'Loan booked with the credit limit',
            'request_type': request_type
        }
        booked_amount = credit_limit

    elif request_type == 'LAD':
        loan_data = {
            'nbfc_id': nbfc_id,
            'loan_id': loan_id,
            'loan_type': loan_type,
            'user_id': user_id,
            'cibil_score': cibil_score,
            'credit_limit': credit_limit,
            'amount': loan_amount,
            'user_type': user_type,
            'is_booked': True,
            'status': 'P'
        }
        loan_log = {
            'request_type': request_type,
            'amount': loan_amount,
            'log_text': 'Loan booked with the actual amount'
        }
        booked_amount = loan_amount
        diff_amount = credit_limit - loan_amount
    else:
        loan_data = {
            'nbfc_id': nbfc_id,
            'loan_type': loan_type,
            'user_id': user_id,
            'cibil_score': cibil_score,
            'credit_limit': credit_limit,
            'user_type': user_type,
        }
        loan_log = {}

    if loan_detail_id:
        loan_data['id'] = loan_detail_id
    loan = LoanDetail(**loan_data)
    loan.save()
    if loan_log:
        LoanBookedLogs(loan=loan, **loan_log)
    if booked_amount:
        booked_data = cache.get('available_balance', {})
        if booked_data:
            booked_value = booked_data.get(nbfc_id, {}).get(user_type)
            if booked_value is not None:
                booked_data[nbfc_id][user_type] -= booked_amount + diff_amount
                booked_data[nbfc_id]['total'] -= booked_amount + diff_amount
            else:
                booked_data[nbfc_id].update({user_type: booked_amount, 'total': booked_amount})
        else:
            booked_data[nbfc_id] = {user_type: booked_amount, 'total': booked_amount}
        cache.set('available_balance', booked_data)

