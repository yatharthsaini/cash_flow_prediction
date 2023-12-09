from datetime import datetime, timedelta
from celery import shared_task
from dateutil.relativedelta import relativedelta

from cash_flow.external_calls import get_due_amount_response, get_collection_poll_response
from cash_flow.models import NbfcWiseCollectionData, ProjectionCollectionData, NbfcBranchMaster
from utils.common_helper import Common


@shared_task()
def populate_json_against_nbfc():
    """
    celery task to populate the models.NbfcWiseCollectionData
    """
    collection_poll_data = get_collection_poll_response().json()
    nbfc_dict = collection_poll_data.get("data", {})

    for key, value in nbfc_dict.items():
        branch_instance = NbfcBranchMaster.objects.filter(branch_name=key).first()
        if branch_instance:
            nfc_wise_collection_data = NbfcWiseCollectionData(
                nbfc=branch_instance,
                collection_json=value
            )
            nfc_wise_collection_data.save()


@shared_task()
def populate_wacm():
    """
    celery task to populate the models.ProjectionCollectionData
    """
    current_date = datetime.now()
    due_date = (current_date + relativedelta(months=1)) - timedelta(1)
    formatted_due_date = due_date.strftime('%Y-%m-%d')
    dd_str = str(due_date.day)
    projection_response_data = get_due_amount_response(formatted_due_date).json().get('data', {})
    nbfc_list = list(projection_response_data.keys())
    nbfc_ids = NbfcBranchMaster.objects.filter(branch_name__in=nbfc_list).order_by('created_at')
    nbfc_ids = dict(nbfc_ids.values_list('branch_name', 'id'))
    nbfc_ids_list = list(nbfc_ids.values())
    queryset = NbfcWiseCollectionData.objects.filter(nbfc_id__in=nbfc_ids_list).order_by('created_at')
    queryset = dict(queryset.values_list('nbfc_id', 'collection_json'))
    for nbfc_id, projection_amount in projection_response_data.items():
        collection_json = queryset.get(nbfc_id, {})
        ce_new_json = collection_json.get(dd_str, {}).get("New", {})
        ce_old_json = collection_json.get(dd_str, {}).get("Old", {})
        wace_dict = Common.get_wace_against_due_date(ce_new_json, ce_old_json)

        for dpd_date in wace_dict.keys():
            dpd_date_str = str(dpd_date)
            collection_date = due_date + timedelta(int(dpd_date))

            # db constraint of not getting the duplicate set of same nbfc, due_date and collection_date
            obj, created = ProjectionCollectionData.objects.get_or_create(
                nbfc_id=nbfc_ids[nbfc_id],
                due_date=due_date,
                collection_date=collection_date,
                defaults={'amount': wace_dict[dpd_date_str] * projection_amount}
            )

            # If the object already existed, update its amount field
            if not created:
                obj.amount = wace_dict[dpd_date_str] * projection_amount
                obj.save()
