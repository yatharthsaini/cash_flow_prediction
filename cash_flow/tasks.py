import os
from json import JSONDecodeError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db import IntegrityError
from django.utils import timezone
from django.core.management import call_command
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.db.models import Sum, When, Case, F
from cash_flow.external_calls import (get_due_amount_response, get_collection_poll_response, get_nbfc_list,
                                      get_collection_amount_response, get_loan_booked_data, get_failed_loan_data)
from cash_flow.models import (NbfcWiseCollectionData, ProjectionCollectionData, NbfcBranchMaster,
                              CollectionAndLoanBookedData, CollectionLogs, LoanDetail, LoanBookedLogs,
                              NBFCEligibilityCashFlowHead)
from utils.common_helper import Common
from cash_flow_prediction.celery import celery_error_email, app


@app.task(bind=True)
@celery_error_email
def populate_json_against_nbfc(self, due_date=None):
    """
    celery task to populate the models.NbfcWiseCollectionData
    """
    if due_date is None:
        current_date = datetime.now().date()
        due_date = current_date + relativedelta(months=1) - timedelta(days=1)
    elif isinstance(due_date, str):
        due_date = datetime.strptime(due_date, '%Y-%m-%d')

    formatted_due_date = due_date.strftime('%Y-%m-%d')
    try:
        collection_poll_data = get_collection_poll_response(formatted_due_date).json()
    except JSONDecodeError as _:
        return

    if collection_poll_data:
        nbfc_dict = collection_poll_data.get("data", {})

        for nbfc_id, json_data in nbfc_dict.items():

            try:
                nbfc_wise_collection_instance = NbfcWiseCollectionData.objects.create(
                    due_date=due_date,
                    nbfc_id=nbfc_id,
                    collection_json=json_data
                )
            except IntegrityError:
                nbfc_wise_collection_instance = NbfcWiseCollectionData.objects.get(
                    nbfc_id=nbfc_id,
                    due_date=due_date
                )
                nbfc_wise_collection_instance.collection_json = json_data
            nbfc_wise_collection_instance.save()


@app.task(bind=True)
@celery_error_email
def populate_wacm(self, due_date=None):
    """
    celery task to populate the models.ProjectionCollectionData
    """
    if due_date is None:
        current_date = datetime.now()
        due_date = current_date + relativedelta(months=1) - timedelta(days=1)
    elif isinstance(due_date, str):
        due_date = datetime.strptime(due_date, '%Y-%m-%d')

    formatted_due_date = due_date.strftime('%Y-%m-%d')
    dd_str = str(due_date.day)
    try:
        projection_response_data = get_due_amount_response(formatted_due_date).json()
    except JSONDecodeError as _:
        return
    if projection_response_data:
        projection_response_data = projection_response_data.get('data', {})
    nbfc_list = list(projection_response_data.keys())
    nbfc_ids = NbfcBranchMaster.objects.filter(id__in=nbfc_list).order_by('created_at')
    nbfc_ids = dict(nbfc_ids.values_list('branch_name', 'id'))
    nbfc_ids_list = list(nbfc_ids.values())
    queryset = NbfcWiseCollectionData.objects.filter(nbfc_id__in=nbfc_ids_list, due_date=due_date).order_by(
        'created_at')
    queryset = dict((str(nbfc_id), collection_json) for nbfc_id, collection_json in
                    queryset.values_list('nbfc_id', 'collection_json'))

    for nbfc_id, projection_amount in projection_response_data.items():
        collection_json = {}
        if nbfc_id in queryset:
            collection_json = queryset[nbfc_id]

        ce_new_json = collection_json.get(dd_str, {}).get("New", {})
        ce_old_json = collection_json.get(dd_str, {}).get("Old", {})

        for dpd_date in range(-7, 46):
            dpd_date_str = str(dpd_date)
            collection_date = due_date + timedelta(int(dpd_date))
            old_ratio = ce_old_json.get(dpd_date_str, 0)
            new_ratio = ce_new_json.get(dpd_date_str, 0)
            total_ratio = old_ratio + new_ratio
            if total_ratio == 0:
                continue
            total_amount = total_ratio * projection_amount
            new_user_amount = new_ratio * projection_amount
            old_user_amount = old_ratio * projection_amount

            try:
                nbfc_instance = NbfcBranchMaster.objects.get(id=nbfc_id)
            except ObjectDoesNotExist:
                continue

            # db constraint of not getting the duplicate set of same nbfc, due_date and collection_date
            ProjectionCollectionData.objects.update_or_create(
                nbfc=nbfc_instance,
                due_date=due_date,
                collection_date=collection_date,
                defaults={'amount': total_amount, 'old_user_amount': old_user_amount,
                          'new_user_amount': new_user_amount, 'due_amount': projection_amount}
            )


@app.task(bind=True)
@celery_error_email
def populate_nbfc_branch_master(self):
    """
    celery task to populate nbfc branch master storing nbfc's with the corresponding id's
    """
    try:
        nbfc_list_data_response = get_nbfc_list().json()
    except JSONDecodeError as _:
        return
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


@app.task(bind=True)
@celery_error_email
def populate_collection_amount(self):
    """
    celery task to populate the collection amount in models.CollectionAndLoanBookedData
    for a nbfc's for a particular due_date
    the celery task would also log the changes into the models.CollectionLogs for every change pre
    celery task and post celery task collection amount
    """
    due_date = datetime.now().date()
    str_due_date = due_date.strftime('%Y-%m-%d')
    try:
        collection_amount_response = get_collection_amount_response(str_due_date).json()
    except JSONDecodeError as _:
        return
    if collection_amount_response:
        collection_amount_data = collection_amount_response.get('data', {})
        for nbfc_id, collection_amount in collection_amount_data.items():

            collection_instance = CollectionAndLoanBookedData.objects.filter(
                nbfc_id=nbfc_id,
                due_date=due_date
            ).first()

            if collection_instance:
                collection_instance.collection = collection_amount
                collection_instance.save()
            else:
                collection_instance = CollectionAndLoanBookedData.objects.create(
                    nbfc_id=nbfc_id,
                    due_date=due_date,
                    collection=collection_amount
                )

            collection_logs = CollectionLogs.objects.filter(collection=collection_instance).first()

            if collection_logs:
                prev_collection = collection_logs.amount
                if prev_collection:
                    collection_amount = collection_amount - prev_collection

            collection_log_instance = CollectionLogs(
                collection=collection_instance,
                amount=collection_amount
            )
            collection_log_instance.save()


@app.task(bind=True)
@celery_error_email
def populate_loan_booked_amount(self):
    """
    celery task to populate the loan_booked amount in models.CCollectionAndLoanBookedData
    for a nbfc's for a particular due_date
    """
    due_date = datetime.now().date()
    str_due_date = due_date.strftime('%Y-%m-%d')
    try:
        loan_booked_response = get_loan_booked_data(str_due_date).json()
    except JSONDecodeError as _:
        return
    if loan_booked_response:
        loan_booked_data = loan_booked_response.get('data', {})
        for nbfc_id, loan_booked in loan_booked_data.items():
            # Try to get an existing record for the NBFC and due_date
            CollectionAndLoanBookedData.objects.update_or_create(
                nbfc_id=nbfc_id,
                due_date=due_date,
                defaults={'loan_booked': loan_booked}
            )


@app.task(bind=True)
@celery_error_email
def unbook_failed_loans(self):
    """
    this celery function will get the data for the failed loans and unbook the loans in models.LoanDetail
    """
    try:
        failed_loans_data = get_failed_loan_data().json()
    except JSONDecodeError as _:
        return
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


@app.task(bind=True)
@celery_error_email
def populate_available_cash_flow(self, nbfc=None):
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

    carry_forward = dict(CollectionAndLoanBookedData.objects.filter(**filtered_dict, due_date=due_date).values_list
                         ('nbfc_id', 'last_day_balance'))
    cal_data = {}
    loan_booked_data = cache.get('loan_booked', {})
    for nbfc_id in prediction_amount_value:
        hold_cash = hold_cash_value.get(nbfc_id, 0)
        if hold_cash == 100:
            continue

        prediction_cash_inflow = prediction_amount_value.get(nbfc_id, 0)
        prev_day_carry_forward = carry_forward.get(nbfc_id, 0)

        capital_inflow = capital_inflow_value.get(nbfc_id, 0)

        available_cash_flow = Common.get_available_cash_flow(prediction_cash_inflow, prev_day_carry_forward,
                                                             capital_inflow, hold_cash)

        nbfc_loan_booked = loan_booked_data.get(nbfc_id, {})
        user_ratio = user_ratio_value.get(nbfc_id, [80, 20])
        old_ratio = user_ratio[0]
        new_ratio = user_ratio[1]

        old_value = (available_cash_flow * old_ratio) / 100
        new_value = (available_cash_flow * new_ratio) / 100

        cal_data[nbfc_id] = {
            'O': old_value - nbfc_loan_booked.get('O', 0),
            'N': new_value - nbfc_loan_booked.get('N', 0),
            'total': available_cash_flow - nbfc_loan_booked.get('total', 0)
        }

    if nbfc:
        return cal_data.get(nbfc, {}).get('total', 0)
    cache.set('available_balance', cal_data, 600)


@app.task(bind=True)
@celery_error_email
def task_for_loan_booked(self, nbfc_id=None):
    """
    celery task for loan booked
    :return:
    """
    filtered_dict = {}
    if nbfc_id:
        filtered_dict['nbfc_id'] = nbfc_id

    due_date = datetime.now().date()
    loan_booked_instance = LoanDetail.objects.filter(updated_at__date=due_date, is_booked=True,
                                                     **filtered_dict).exclude(status='F')
    loan_booked_instance = loan_booked_instance.annotate(
        value=Case(
            When(status='P', then=F('amount')),
            default=F('credit_limit')
        )
    )
    loan_booked_instance = loan_booked_instance.values('nbfc_id', 'user_type').order_by('nbfc_id').annotate(
        total_amount=Sum('value')
    )
    loan_booked = loan_booked_instance.values_list('nbfc_id', 'total_amount', 'user_type')
    booked_data = {}
    for i in loan_booked:
        if i not in booked_data:
            booked_data[i[0]] = {
                'O': 0,
                'N': 0,
                'total': 0
            }
        booked_data[i[0]][i[2]] += i[1]
        booked_data[i[0]]['total'] += i[1]

    if nbfc_id:
        return booked_data.get(nbfc_id, {}).get('total', 0)
    cache.set('loan_booked', booked_data, 600)


@app.task(bind=True)
@celery_error_email
def task_for_loan_booking(self, credit_limit, loan_type, request_type, user_id, user_type, cibil_score,
                          nbfc_id, age, prev_loan_status=None, is_booked=False, loan_amount=None,
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
    :param is_booked:
    :param cibil_score:
    :param prev_loan_status:
    :param loan_amount:
    :param nbfc_id: nbfc to be booked in the loan detail
    :param loan_id:
    :param age:
    :return:
    """
    due_date = datetime.now().date()
    diff_amount = 0
    booked_amount = 0
    current_loan_status = None
    if request_type == 'LAN':
        current_loan_status = 'I'
        loan_data = {
            'nbfc_id': nbfc_id,
            'user_id': user_id,
            'cibil_score': cibil_score,
            'credit_limit': credit_limit,
            'loan_type': loan_type,
            'loan_id': loan_id,
            'user_type': user_type,
            'is_booked': True,
            'status': 'I',
            'age': age
        }
        loan_log = {
            'amount': credit_limit,
            'log_text': 'Loan booked with the credit limit',
            'request_type': request_type
        }
        booked_amount = credit_limit
        diff_amount = credit_limit

    elif request_type == 'LAD':
        current_loan_status = 'P'
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
            'status': 'P',
            'age': age
        }
        loan_log = {
            'request_type': request_type,
            'amount': loan_amount,
            'log_text': 'Loan booked with the actual amount'
        }
        booked_amount = loan_amount
        diff_amount = loan_amount - credit_limit
    else:
        loan_data = {
            'nbfc_id': nbfc_id,
            'loan_type': loan_type,
            'user_id': user_id,
            'cibil_score': cibil_score,
            'credit_limit': credit_limit,
            'user_type': user_type,
            'age': age
        }
        loan_log = {}
    user_loan = LoanDetail.objects.filter(user_id=user_id, created_at__date=due_date).exclude(status='F')
    if user_loan.exists():
        loan = user_loan.first()
        for i in loan_data:
            setattr(loan, i, loan_data[i])
        loan.save()
    else:
        loan = LoanDetail(**loan_data)
        loan.save()
    if loan_log:
        LoanBookedLogs.objects.create(loan=loan, **loan_log)
    if booked_amount and (is_booked is False or prev_loan_status != current_loan_status):
        booked_data = cache.get('available_balance', {})
        if booked_data:
            booked_value = booked_data.get(nbfc_id, {}).get(user_type)
            if booked_value is not None:
                booked_data[nbfc_id][user_type] -= diff_amount
                booked_data[nbfc_id]['total'] -= diff_amount
            else:
                booked_data[nbfc_id].update({user_type: booked_amount, 'total': booked_amount})
        else:
            booked_data[nbfc_id] = {user_type: booked_amount, 'total': booked_amount}
        cache.set('available_balance', booked_data)


@app.task(bind=True)
@celery_error_email
def populate_last_day_balance(self, nbfc=None):
    """
    celery task to populate last day balance in models.ProjectionCollectionData
    required things to calculate prev day carry forward are: collection amount, capital inflow, hold_cash,
    loan_booked
    """
    filtered_dict = {}
    today = datetime.now().date()
    due_date = today - timedelta(days=1)
    if nbfc:
        filtered_dict['nbfc_id'] = nbfc
    prediction_amount_value = dict(ProjectionCollectionData.objects.filter(
        **filtered_dict,
        collection_date=due_date).values('nbfc_id').order_by('nbfc_id').annotate(
        total_amount=Sum('amount')
    ).values_list('nbfc_id', 'total_amount'))

    hold_cash_value = Common.get_hold_cash_value(due_date)
    capital_inflow_value = Common.get_nbfc_capital_inflow(due_date)

    last_day_balance_data = dict(CollectionAndLoanBookedData.objects.filter(due_date=due_date, **filtered_dict).
                                 values_list('nbfc_id', 'last_day_balance'))
    loan_booked_instance = LoanDetail.objects.filter(updated_at__date=due_date, is_booked=True,
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
    loan_booked_dict = dict(loan_booked_instance.values_list('nbfc_id', 'total_amount'))

    prev_due_date = due_date - timedelta(days=1)

    for nbfc_id in last_day_balance_data:
        last_day_balance = last_day_balance_data.get(nbfc_id, 0)
        hold_cash = hold_cash_value.get(nbfc_id, 0)

        prediction_cash_inflow = prediction_amount_value.get(nbfc_id, 0)
        prev_day_carry_forward = last_day_balance

        capital_inflow = capital_inflow_value.get(nbfc_id, 0)
        available_cash_flow = Common.get_available_cash_flow(prediction_cash_inflow, prev_day_carry_forward,
                                                             capital_inflow, hold_cash)

        loan_booked = loan_booked_dict.get(nbfc_id, 0)

        if loan_booked is None:
            loan_booked = 0

        last_day_balance = available_cash_flow - loan_booked
        CollectionAndLoanBookedData.objects.update_or_create(
            nbfc_id=nbfc_id,
            due_date=today,
            defaults={'last_day_balance': last_day_balance}
        )


@app.task(bind=True)
@celery_error_email
def task_to_validate_loan_booked(self):
    """
    celery task to validate loan booked
    :return:
    """
    current_time = timezone.now()
    time_to_be_checked = current_time - timedelta(hours=3)
    loans_to_be_unbooked = LoanDetail.objects.filter(updated_at__lte=time_to_be_checked,
                                                     status='I', is_booked=True).order_by('nbfc_id')
    bulk_update = []
    for i in loans_to_be_unbooked:
        user_type = i.user_type
        nbfc_id = i.nbfc_id
        amount = i.credit_limit
        available_balance = cache.get('available_balance', {})
        value = available_balance.get(nbfc_id, {}).get(user_type, 0)
        amount += value

        available_balance.setdefault(nbfc_id, {})[user_type] = amount
        cache.set('available_balance', available_balance)

        lb = LoanBookedLogs(
            loan=i,
            request_type='BE',
            amount=amount,
            log_text='Unbooking after three hours of inactivity'
        )
        bulk_update.append(lb)

    loans_to_be_unbooked.update(is_booked=False)
    LoanBookedLogs.objects.bulk_create(bulk_update, batch_size=100)


@app.task(bind=True)
@celery_error_email
def run_migrate(self, password=None):
    if password is None:
        raise ValueError("Password is required to run the migrate task.")
    expected_password = os.environ.get('MIGRATE_PASSWORD')
    if password != expected_password:
        raise ValueError("Invalid password")
    call_command('migrate')


def populate_should_assign_should_check_cache():
    """
    celery cron to populate should assign and should check in cache
    :return:
    """
    try:
        should_check_branches = set(
            NBFCEligibilityCashFlowHead.objects.filter(should_check=True).values_list('nbfc_id', flat=True))
        cache.set('should_check', list(should_check_branches), timeout=172800)
        should_assign_branches = set(
            NBFCEligibilityCashFlowHead.objects.filter(should_assign=True).values_list('nbfc_id', flat=True))
        cache.set('should_assign', list(should_assign_branches), timeout=172800)
    except Exception as e:
        print(e)
