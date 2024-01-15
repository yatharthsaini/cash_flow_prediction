from datetime import date, timedelta, datetime
from django.db.models import Sum
from django.conf import settings

import cash_flow.models
from cash_flow.models import (CollectionAndLoanBookedData, ProjectionCollectionData,
                              CapitalInflowData, HoldCashData, NbfcBranchMaster, LoanDetail, LoanBookedLogs)
from cash_flow.external_calls import get_cash_flow_data


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
    def get_collection_and_loan_booked(nbfc_id: int, due_date: date) -> [float, float]:
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
        loan_booked = 0.0
        if collection_and_loan_booked_instance:
            collection = collection_and_loan_booked_instance.collection
            loan_booked = collection_and_loan_booked_instance.loan_booked
        return collection, loan_booked

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
            variance = ((predicted_cash_inflow - collection) / predicted_cash_inflow) / 100
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

    @staticmethod
    def get_nbfc_having_lowest_average_for_delay_in_disbursal(available_credit_line_branches: list) -> int:
        """
        function that returns the nbfc_id with the lowest delay in disbursal average
        :param available_credit_line_branches: a list carrying ids representing nbfc_ids
        :return: an integer representing the nbfc_id
        """
        lowest_delay = float('inf')  # Initialize with positive infinity
        lowest_delay_nbfc_id = -1

        for nbfc_id in available_credit_line_branches:
            master_branch_instance = NbfcBranchMaster.objects.get(id=nbfc_id)

            if (master_branch_instance.delay_in_disbursal is not None and
                    master_branch_instance.delay_in_disbursal < lowest_delay):
                lowest_delay = master_branch_instance.delay_in_disbursal
                lowest_delay_nbfc_id = nbfc_id

        return lowest_delay_nbfc_id

    def get_nbfc_for_loan_to_be_booked(self, branches_list: list, sanctioned_amount: float,
                                       due_date: date = datetime.now(),
                                       user_type: str = True) -> int:
        """
        this helper function helps to get the nbfc id for the loan to be booked if the user
        is new or old, and checking other conditions if there is available credit line or not
        :param due_date: a date field representing the date field
        :param user_type: string that tells if a user is new or old as 'O' or 'N'
        :param branches_list: a list containing nbfc_id's representing eligible branches
        :param sanctioned_amount: a float representing sanctioned/applied amount
        :return: the nbfc id as an integer field, it will return -1 in case of no nbfc is found
        """
        available_credit_line_branches = []
        overbooked_data = []
        str_due_date = due_date.strftime('%Y-%m-%d')
        for branch_id in branches_list:
            cash_flow_data = get_cash_flow_data(branch_id, str_due_date).json()
            if cash_flow_data:
                available_credit_line = cash_flow_data.get('available_cash_flow', None)
                if user_type == 'O':
                    old_user_percentage = cash_flow_data.get('old_user_percentage', None)
                    available_credit_line = (available_credit_line * old_user_percentage) / 100
                else:
                    new_user_percentage = cash_flow_data.get('new_user_percentage', None)
                    available_credit_line = (available_credit_line * new_user_percentage) / 100

                if available_credit_line >= sanctioned_amount:
                    available_credit_line_branches.append(branch_id)
                else:
                    overbooked_amount = (sanctioned_amount - available_credit_line)
                    if available_credit_line != 0:
                        over_booked_ratio = overbooked_amount / available_credit_line
                        overbooked_data.append(
                            {
                                'id': branch_id,
                                'ratio': over_booked_ratio
                            }
                        )

        if len(available_credit_line_branches) != 0:
            return self.get_nbfc_having_lowest_average_for_delay_in_disbursal(available_credit_line_branches)

        if len(overbooked_data) != 0:
            min_overbooked_ratio_branch = min(overbooked_data, key=lambda x: x['ratio'])
            return min_overbooked_ratio_branch['id']
        return -1

    @staticmethod
    def block_nbfcs_having_full_hold_cash(eligible_branches_list: list, due_date: date) -> list:
        """
        helper to return a refined list by blocking nbfcs having full hold cash from the eligible_branches_list
        :param eligible_branches_list: a list
        :param due_date: a date-field
        :return:
        """
        nbfcs_to_be_blocked = []
        for nbfc in eligible_branches_list:
            hold_cash_instance = cash_flow.models.HoldCashData.objects.filter(nbfc=nbfc,
                                                                              start_date__lte=due_date,
                                                                              end_date__gte=due_date).first()
            if hold_cash_instance:
                if hold_cash_instance.hold_cash == 100:
                    nbfcs_to_be_blocked.append(nbfc)
        return [x for x in eligible_branches_list if x not in nbfcs_to_be_blocked]

    @staticmethod
    def block_nbfcs_that_are_to_be_blocked(eligible_branches_list: list) -> list:
        """
        this helper function returns the refined nbfc list ny blocking the nbfcs that are to be blocked
        like that of Unity
        :param eligible_branches_list: a list containing eligible nbfcs
        :return: a further refined list containing nbfcs
        """
        nbfcs_to_be_blocked = settings.NO_CHANGE_NBFC_LIST
        return [x for x in eligible_branches_list if x not in nbfcs_to_be_blocked]

    @staticmethod
    def book_the_loan_instance_with_the_logs(credit_limit, loan_type, request_type, user_id, user_type, cibil_score,
                                             nbfc, loan_amount=None, is_booked=False,
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
        :param is_booked:
        :param nbfc: nbfc to be booked in the loan detail
        :param loan_id:
        :return:
        """
        if request_type == 'LAN':
            # booking the loan instance with the loan status I and loan_id is None
            nbfc_master_instance = NbfcBranchMaster.objects.filter(id=nbfc).first()
            if nbfc_master_instance:
                loan_instance = LoanDetail(
                    nbfc=nbfc_master_instance,
                    loan_id=loan_id,
                    user_id=user_id,
                    cibil_score=cibil_score,
                    credit_limit=credit_limit,
                    amount=credit_limit,
                    loan_type=loan_type,
                    user_type=user_type,
                    is_booked=is_booked,
                    status='I'
                )
                loan_instance.save()
                # logging the loan logs
                loan_log_instance = LoanBookedLogs(
                    loan=loan_instance,
                    amount=credit_limit,
                    log_text='Loan booked with the credit limit',
                    request_type=request_type
                )
                loan_log_instance.save()
        elif request_type == 'LAD':
            # booking the actual amount to be booked
            nbfc_master_instance = NbfcBranchMaster.objects.filter(id=nbfc).first()
            if  nbfc_master_instance:
                loan_detail_instance = LoanDetail(
                    nbfc=nbfc_master_instance,
                    loan_id=loan_id,
                    loan_type=loan_type,
                    user_id=user_id,
                    cibil_score=cibil_score,
                    credit_limit=credit_limit,
                    loan_amount=loan_amount,
                    user_type=user_type,
                    is_booked=is_booked,
                    status='P'
                )
                loan_detail_instance.save()

                loan_log_instance = LoanBookedLogs(
                    loan=loan_detail_instance,
                    request_type=request_type,
                    amount=loan_amount,
                    log_text='Loan booked with the actual amount'
                )
                loan_log_instance.save()

    @staticmethod
    def unbook_the_failed_loan(loan_id):
        """
        this function unbooks the loan id as the loan is being failed in models.LoanDetail and also logging in
        models.LoanBookedLogs
        :param loan_id: the int representing the loan id
        :return:
        """
        loan_detail_instance = LoanDetail.objects.filter(loan_id=loan_id).first()
        if loan_detail_instance:
            loan_detail_instance.status = 'F'
            unbooked_amount = loan_detail_instance.amount
            loan_log_instance = LoanBookedLogs(
                loan=loan_detail_instance,
                amount=unbooked_amount,
                request_type='LF',
                log_text='Unbooking the amount due to loan failure'
            )
            loan_log_instance.save()
            # and also un_booking the loan amount
            loan_detail_instance.delete()







