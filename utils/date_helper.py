from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


def convert_string_to_date_field(due_date: str, dpd_date: str) -> (date, date):
    """
    function for converting a string representation into a date field to be stored in model as DateField and
    also returning the collection_date where collection_date is :
        collection_date = due_date + dpd_date
    :param due_date: a string containing due_date
    :param dpd_date: a string containing dpd_date
    :return: a date field object of due date and a date object of collection_date too
    """
    date_field_due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
    collection_date = date_field_due_date + timedelta(days=int(dpd_date))
    return date_field_due_date, collection_date


def get_due_date():
    """
    function that returns due_date as : current date + (1 month and -1 day) from the current date
    """
    current_date = datetime.now()
    due_date = current_date + relativedelta(months=1, days=-1)
    return due_date.strftime("%Y-%m-%d")


def get_dd_str(due_date: str) -> str:
    """
    function to return the dd string only extracted from the YYYY-MM-DD
    :param due_date: a string in the format "YYYY-MM-DD"
    """
    due_date_datetime = datetime.strptime(due_date, "%Y-%m-%d")
    dd_int = due_date_datetime.day
    return str(dd_int)

