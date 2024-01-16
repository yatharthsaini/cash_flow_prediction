from typing import Any
import requests
from django.conf import settings


def get_common_headers():
    """
    common headers function
    """
    return {
        "token": settings.COLLECTION_PREDICTION_TOKEN
    }


def get_collection_poll_response() -> Any:
    """
    External api for getting the collection poll data
    :return: json response
    """
    url = settings.COLLECTION_PREDICTION_POLL_URL
    headers = get_common_headers()
    response = requests.get(url=url, headers=headers, timeout=200)
    return response


def get_due_amount_response(due_date: str) -> Any:
    """
    external call for getting the due amount for different nbfc's
    :return: json response
    """
    url = settings.DUE_AMOUNT_URL
    headers = get_common_headers()
    params = {
        "date": due_date
    }
    response = requests.get(url=url, headers=headers, params=params, timeout=300)
    return response


def get_nbfc_list() -> Any:
    """
    external call for getting the nbfc_list with the corresponding id's
    :return: json response
    """
    url = settings.NBFC_LIST_URL
    headers = get_common_headers()
    response = requests.get(url=url, headers=headers, timeout=300)
    return response


def get_collection_amount_response(due_date: str) -> Any:
    """
    external call for getting the collection amount data for a particular due_date
    :return: json response
    """
    url = settings.COLLECTION_AMOUNT_URL
    headers = get_common_headers()
    params = {
        "date": due_date
    }
    response = requests.get(url=url, headers=headers, params=params, timeout=300)
    return response


def get_loan_booked_data(due_date: str) -> Any:
    """
    external call for getting the loan booked amount data for a particular due_date
    return: json response
    """
    url = settings.LOAN_BOOKED_URL
    headers = get_common_headers()
    params = {
        "date": due_date
    }
    response = requests.get(url=url, headers=headers, params=params, timeout=300)
    return response


def get_failed_loan_data() -> Any:
    """
    external call getting the failed loan data
    :return: json response
    """
    url = settings.FAILED_LOAN_DATA
    headers = get_common_headers()
    response = requests.get(url=url, headers=headers, timeout=300)
    return response
