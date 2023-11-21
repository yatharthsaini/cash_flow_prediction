from typing import Any
import requests
from django.conf import settings


def get_collection_poll_response() -> Any:
    """
    External api for getting the collection poll data
    :return: json response
    """
    url = settings.COLLECTION_PREDICTION_POLL_URL
    headers = {
        "token": settings.COLLECTION_PREDICTION_TOKEN
    }
    response = requests.get(url=url, headers=headers)
    return response


def get_due_amount_response(due_date: str) -> Any:
    """
    external call for getting the due amount for different nbfc's
    :return: json response
    """
    url = settings.DUE_AMOUNT_URL
    headers = {
        "token": settings.COLLECTION_PREDICTION_TOKEN
    }
    params = {
        "date": due_date
    }
    response = requests.get(url=url, headers=headers, params=params)
    return response
