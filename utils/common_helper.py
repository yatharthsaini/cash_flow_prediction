import json
import os
import base64
import glob

from datetime import date, timedelta, datetime
from django.db.models import Sum
from django.db.models import Q
from django.core.cache import cache
from cash_flow.models import (CollectionAndLoanBookedData, ProjectionCollectionData,
                              CapitalInflowData, HoldCashData, NbfcBranchMaster,
                              UserRatioData)


class Common:
    @staticmethod
    def get_wace_against_due_date(ce_json_new: dict, ce_json_old: dict) -> dict:
        """
        helper function to find the (WACE) weighted average collection efficiency for a particular due date using
        new user's collection efficiency data and old user's collection efficiency data
        :param ce_json_new: collection efficiencies for new users for a particular nbfc for a particular date
        :param ce_json_old: collection efficiencies for new users for a particular nbfc for a particular date
        collection efficiencies in both dicts are in floats like 0.045, 0.0007, 0.25 etc.
        :return: a json containing ce's we for all dps ( Delay in payment date) for a particular due_date
        Weighted Average Collection Efficiency= [(%of loans given to new user * CE)+(%of loans given to old user * CE)]
        """
        wace_dict = {}
        for dpd in range(-7, 46):
            ce_avg = 0
            str_dpd = str(dpd)
            ce_avg += ce_json_new.get(str_dpd, 0)
            ce_avg += ce_json_old.get(str_dpd, 0)

            wace_dict[str_dpd] = ce_avg

        return wace_dict

    @staticmethod
    def get_collection_and_last_day_balance(nbfc_id: int, due_date: date) -> [float, float]:
        """
        helper function to get the collection amount from the models.NbfcAndDateWiseCashFlowData filtered
        against the nbfc_id name and the due_date
        :param nbfc_id: an int holding the nbfc_id
        :param due_date: a string holding the due date
        :return: collection param and loan_booked returned from the models.NbfcAndDateWiseCashFlowData
        """
        collection_and_loan_booked_instance = CollectionAndLoanBookedData.objects.filter(
            nbfc_id=nbfc_id,
            due_date=due_date
        ).order_by('created_at').first()

        collection = 0.0
        last_day_balance = 0.0
        if collection_and_loan_booked_instance:
            collection = collection_and_loan_booked_instance.collection
            last_day_balance = collection_and_loan_booked_instance.last_day_balance
        return collection, last_day_balance

    @staticmethod
    def get_predicted_cash_inflow(nbfc_id: int, due_date: date) -> float:
        """
        function to return the predicted cash inflow for a particular nbfc and a particular due_date
        :param nbfc_id : an int value storing the nbfc_id
        :param due_date : a string value storing the due date
        :return: predicted cash inflow which is the summation of all the predicted amount from
        models.ProjectionCollectionData
        """
        projection_collection_instance = ProjectionCollectionData.objects.filter(
            nbfc=nbfc_id,
            due_date=due_date
        ).first()
        amount = 0.0
        if projection_collection_instance:
            amount = ProjectionCollectionData.objects.filter(
                nbfc=nbfc_id,
                due_date=due_date
            ).aggregate(Sum('amount'))['amount__sum']
        return amount

    @staticmethod
    def get_prev_day_carry_forward(nbfc_id: int, due_date: date) -> float:
        """
        this function is used for calculating the prev day carry forward using filters of prev day on
        capital_inflow, hold_cash, loan_booked, and collection
        :param nbfc_id: an int representing the nbfc_id
        :param due_date: a date field representing due_date
        :return: a float val for carry_forward
        """
        prev_day = due_date - timedelta(days=1)
        prev_day_capital_inflow = 0.0
        prev_day_capital_inflow_instance = CapitalInflowData.objects.filter(nbfc_id=nbfc_id,
                                                                            start_date__lte=prev_day,
                                                                            end_date__gte=prev_day).first()
        if prev_day_capital_inflow_instance:
            prev_day_capital_inflow = prev_day_capital_inflow_instance.capital_inflow

        prev_day_hold_cash = 0.0
        prev_day_hold_cash_instance = HoldCashData.objects.filter(nbfc_id=nbfc_id,
                                                                  start_date__lte=prev_day,
                                                                  end_date__gte=prev_day).first()
        if prev_day_hold_cash_instance:
            prev_day_hold_cash = prev_day_hold_cash_instance.hold_cash

        prev_day_collection = 0.0
        prev_day_loan_booked = 0.0
        prev_day_collection_and_loan_booked_instance = CollectionAndLoanBookedData.objects.filter(nbfc_id=nbfc_id,
                                                                                                  due_date=prev_day).first()

        if prev_day_collection_and_loan_booked_instance:
            prev_day_collection = prev_day_collection_and_loan_booked_instance.collection
            prev_day_loan_booked = prev_day_collection_and_loan_booked_instance.loan_booked

        return Common.get_carry_forward(prev_day_collection, prev_day_capital_inflow,
                                        prev_day_hold_cash, prev_day_loan_booked)

    @staticmethod
    def get_carry_forward(collection: float,
                          capital_inflow: float, hold_cash: float,
                          loan_booked: float) -> [float]:
        """
        :param collection:  float value for collection
        :param capital_inflow: float value for capital_inflow
        :param hold_cash: float value for hold_cash
        :param loan_booked: float value for loan_booked
        :return: carry_forward
        """
        collection = collection if collection is not None else 0.0
        capital_inflow = capital_inflow if capital_inflow is not None else 0.0
        hold_cash = hold_cash if hold_cash is not None else 0.0
        loan_booked = loan_booked if loan_booked is not None else 0.0

        carry_forward = (collection + capital_inflow) * (1 - (hold_cash / 100)) + loan_booked
        if carry_forward is None:
            return 0
        return carry_forward

    @staticmethod
    def get_real_time_variance(predicted_cash_inflow: float, collection: float) -> float:
        """
        function for returning the real time variance from predicted_cash_inflow and the collection values
        :param predicted_cash_inflow: float val calculated in the db
        :param collection: a real time float we are getting from a celery task
        :return: float value for variance which is also real time as it is a function of collection param
        """
        variance = 0
        if predicted_cash_inflow != 0:
            variance = ((predicted_cash_inflow - collection) / predicted_cash_inflow) * 100
        return variance

    @staticmethod
    def get_available_cash_flow(predicted_cash_inflow: float, prev_day_carry_forward: float,
                                capital_inflow: float, hold_cash: float) -> float:
        """helper function to compute the available cash flow using predicted_cash_inflow, capital inflow,
        hold cash and carry_forward of previous day
        :param predicted_cash_inflow: predicted float value
        :param prev_day_carry_forward: carry forward mapped from the previous day, a float value
        :param capital_inflow: user input float value
        :param hold_cash: user input float value
        :return: available cash flow as a float
        """
        available_cash_flow = (predicted_cash_inflow + prev_day_carry_forward + capital_inflow) * (
                1 - (hold_cash / 100))
        if available_cash_flow is None:
            return 0.0
        return available_cash_flow

    def get_nbfc_for_loan_to_be_booked(self, branches_list: list, sanctioned_amount: float,
                                       user_type: str = True):
        """
        this helper function helps to get the nbfc id for the loan to be booked if the user
        is new or old, and checking other conditions if there is available credit line or not
        :param user_type: string that tells if a user is new or old as 'O' or 'N'
        :param branches_list: a list containing nbfc_id's representing eligible branches
        :param sanctioned_amount: a float representing sanctioned/applied amount
        :return: the nbfc id as an integer field, it will return -1 in case of no nbfc is found
        """

        delay_in_disbursal = dict(NbfcBranchMaster.objects.filter(id__in=branches_list, delay_in_disbursal__isnull=False
                                    ).order_by('delay_in_disbursal').values_list('id', 'delay_in_disbursal'))
        available_credit_line = cache.get('available_balance', {})
        selected_credit_line = [
            i if available_credit_line.get(i, {}).get(user_type, 0) >= sanctioned_amount else None
            for i in branches_list
        ]
        selected_credit_line = list(set(selected_credit_line))
        selected_credit_line.remove(None) if None in selected_credit_line else None

        if len(selected_credit_line) == 1:
            return selected_credit_line[0]

        if selected_credit_line:
            i = selected_credit_line[0]
            val = delay_in_disbursal.get(i, 0)
            for k in range(1, len(selected_credit_line)):
                j = selected_credit_line[k]
                if val < delay_in_disbursal.get(j, 0):
                    i = j
                    val = delay_in_disbursal.get(j, 0)

            return i

        or_ratio = {
            i: (available_credit_line[i][user_type] + sanctioned_amount)/available_credit_line[i][user_type]
            for i in branches_list
        }
        or_ratio = dict(sorted(or_ratio.items(), key=lambda items: items[1]))

        for i in or_ratio:
            return i

    @staticmethod
    def unbook_the_failed_loan(loan_id):
        """
        this function unbooks the loan id as the loan is being failed in models.LoanDetail and also logging in
        models.LoanBookedLogs
        :param loan_id: the int representing the loan id
        :return:
        """

    @staticmethod
    def get_nbfc_capital_inflow(due_date: date, nbfc_id=None):
        """

        :param nbfc_id:
        :param due_date:
        :return:
        """
        filtered_dict = {}
        if nbfc_id:
            filtered_dict['nbfc_id'] = nbfc_id
        capital_inflow_value = dict(CapitalInflowData.objects.filter(
            Q(start_date=due_date, end_date__isnull=True) | Q(start_date__lte=due_date, end_date__gte=due_date,
                                                              end_date__isnull=False), **filtered_dict
        ).values_list('nbfc_id', 'capital_inflow'))

        if nbfc_id:
            return capital_inflow_value.get(nbfc_id, 0)
        return capital_inflow_value

    @staticmethod
    def get_hold_cash_value(due_date: date, nbfc_id=None):
        """

        :param nbfc_id:
        :param due_date:
        :return:
        """
        filtered_dict = {}
        if nbfc_id:
            filtered_dict['nbfc_id'] = nbfc_id
        hold_cash_value = dict(HoldCashData.objects.filter(
            Q(start_date=due_date, end_date__isnull=True) | Q(start_date__lte=due_date, end_date__gte=due_date,
                                                              end_date__isnull=False), **filtered_dict
        ).values_list('nbfc_id', 'hold_cash'))

        if nbfc_id:
            return hold_cash_value.get(nbfc_id, 0)
        return hold_cash_value

    @staticmethod
    def get_user_ratio(due_date: date, nbfc_id=None):
        """

        :param nbfc_id:
        :param due_date:
        :return:
        """
        filtered_dict = {}
        if nbfc_id:
            filtered_dict['nbfc_id'] = nbfc_id
        user_ratio_instance = UserRatioData.objects.filter(
            Q(start_date=due_date, end_date__isnull=True) | Q(start_date__lte=due_date, end_date__gte=due_date,
                                                              end_date__isnull=False), **filtered_dict
        ).values_list('nbfc_id', 'old_percentage', 'new_percentage')

        user_ratio_value = {}
        for item in user_ratio_instance:
            item_list = list(item)
            nbfc_id = item_list.pop(0)
            user_ratio_value[nbfc_id] = tuple(item_list)

        if nbfc_id:
            return user_ratio_value.get(nbfc_id, [80, 20])
        return user_ratio_value


def calculate_age(dob):
    """
    :param dob: will be coming in the format of yyyy-mm-dd
    :return: the age calculated from the dob
    """

    dob_date = datetime.strptime(dob, '%Y-%m-%d')
    current_date = datetime.now()

    age = current_date.year - dob_date.year - (
                (current_date.month, current_date.day) < (dob_date.month, dob_date.day))

    return age


def save_log_response_for_booking_api(payload, response):
    """
    This helper function saves the log response in the log file every time the cash flow API is being hit.
    """
    log_directory = "logs"
    current_time = datetime.now()
    current_date = current_time.strftime("%Y-%m-%d")
    log_file_name = f"book_nbfc-logs-{current_date}.txt"
    log_file_path = os.path.join(log_directory, log_file_name)

    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    kyc_data = {
        'ckyc': payload.get('ckyc'),
        'ekyc': payload.get('ekyc'),
        'mkyc': payload.get('mkyc')
    }
    log_entry = (f"current_time:{current_time} ---> request_type:{payload.get('request_type', None)} ---> "
                 f"loan_id:{payload.get('loan_id', None)} ---> "f"user_id:{payload.get('user_id', None)} ---> "
                 f"dob:{payload.get('dob', None)} ---> kyc_data:{json.dumps(kyc_data)} ---> "
                 f"response_data:{json.dumps(response.data)} ---> "f"status_code:{response.status_code}")

    with open(log_file_path, "a") as file:
        file.write(log_entry + "\n")


def fetch_file_with_date_and_request_type(date, request_type=None):
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d")
    logs_dir = "logs"
    file_pattern = os.path.join(logs_dir, f'*{date.strftime("%Y-%m-%d")}*')

    matching_files = glob.glob(file_pattern)

    if matching_files:
        file_path = matching_files[0]
        # Open the file
        with open(file_path, 'r') as file:
            if request_type:
                # Filter lines only if request_type is provided
                filtered_lines = [line.strip() for line in file if f'request_type:{request_type}' in line]
            else:
                # If request_type is None, include all lines
                filtered_lines = [line.strip() for line in file]

        filtered_contents = '\n'.join(filtered_lines)

        base64_contents = base64.b64encode(filtered_contents.encode('utf-8')).decode('utf-8')
        data_url = f'data:text/plain;base64,{base64_contents}'
        return data_url
    else:
        return None


def create_kyc_filter(ckyc=False, ekyc=False, mkyc=False) -> Q:
    """
    :param ckyc: true/ false
    :param ekyc: true/false
    :param mkyc: true/false
    :return: a filter
    """
    kyc_filter = Q()
    kyc_filter |= Q(ckyc=True) if ckyc is True else Q(ckyc=None)
    kyc_filter |= Q(ekyc=True) if ekyc is True else Q(ekyc=None)
    kyc_filter |= Q(mkyc=True) if mkyc is True else Q(mkyc=None)
    return kyc_filter
