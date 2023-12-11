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


def get_nbfc_list() -> Any:
    """
    external call for getting the nbfc_list with the corresponding id's
    :return: json response
    """
    url = settings.NBFC_LIST_URL
    headers = {
        "token": settings.COLLECTION_PREDICTION_TOKEN
    }
    response = requests.get(url=url, headers=headers)
    return response


def get_collection_amount_response(due_date: str) -> Any:
    """
    external call for getting the collection amount data for a particular due_date
    :return: json response
    """
    url = settings.COLLECTION_AMOUNT_URL
    headers = {
        "token": settings.COLLECTION_PREDICTION_TOKEN
    }
    params = {
        "date": due_date
    }
    response = requests.get(url=url, headers=headers, params=params)
    return response


def get_loan_booked_data(due_date: str) -> Any:
    """
    external call for getting the loan booked amount data for a particular due_date
    return: json response
    """
    url = settings.LOAN_BOOKED_URL
    headers = {
        "token": settings.COLLECTION_PREDICTION_TOKEN
    }
    params = {
        "date": due_date
    }
    response = requests.get(url=url, headers=headers, params=params)
    return response


def get_cash_flow_data(nbfc_id: int, due_date: str) -> Any:
    """
    external call for getting the cash_flow_data for a particular nbfc_id and due_date
    """
    url = settings.CASH_FLOW_URL
    payload = {
        'nbfc_id': nbfc_id,
        'due_date': due_date
    }
    response = requests.get(url=url, data=payload)
    return response


