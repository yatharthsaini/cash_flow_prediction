from datetime import datetime, timedelta
from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist

from cash_flow.external_calls import (get_due_amount_response, get_collection_poll_response, get_nbfc_list,
                                      get_collection_amount_response, get_loan_booked_data)
from cash_flow.models import (NbfcWiseCollectionData, ProjectionCollectionData, NbfcBranchMaster,
                              CollectionAndLoanBookedData, CollectionLogs)
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
                pre_saved_collection_amount = CollectionAndLoanBookedData.objects.filter(
                    nbfc=nbfc_instance,
                    due_date=due_date
                ).first().collection
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
