from celery import shared_task
from cash_flow.external_calls import get_due_amount_response, get_collection_poll_response
from cash_flow.models import NbfcWiseCollectionData, ProjectionCollectionData
from utils.date_helper import convert_string_to_date_field, get_due_date, get_dd_str
from utils.common_helper import Common


@shared_task()
def populate_json_against_nbfc():
    """
    celery task to populate the models.NbfcWiseCollectionData
    """
    collection_poll_data = get_collection_poll_response().json()
    nbfc_dict = collection_poll_data.get("data", {})

    for key, value in nbfc_dict.items():
        nfc_wise_collection_data = NbfcWiseCollectionData(
            nbfc=key,
            collection_json=value
        )
        nfc_wise_collection_data.save()


@shared_task()
def populate_wacm():
    """
    celery task to populate the models.ProjectionCollectionData
    """
    due_date = get_due_date()
    dd_str = get_dd_str(due_date)
    projection_response_data = get_due_amount_response(due_date).json().get('data', {})
    for nbfc, projection_amount in projection_response_data.items():
        queryset = NbfcWiseCollectionData.objects.filter(nbfc=nbfc)
        if queryset.exists():
            obj = queryset.first()
        else:
            obj = NbfcWiseCollectionData.objects.create(nbfc=nbfc)
        collection_json = obj.collection_json
        ce_new_json = collection_json.get(dd_str).get("New", {})
        ce_old_json = collection_json.get(dd_str).get("Old", {})
        wace_dict = Common.get_wace_against_due_date(ce_new_json, ce_old_json)

        for dpd_date in wace_dict.keys():
            projection_collection_data = ProjectionCollectionData(
                nbfc=obj,
                due_date=convert_string_to_date_field(due_date, dpd_date)[0],
                collection_date=convert_string_to_date_field(due_date, dpd_date)[1],
                amount=wace_dict[dpd_date] * projection_amount
            )
            projection_collection_data.save()
