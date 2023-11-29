from datetime import date
from django.db.models import Sum
from cash_flow.models import NbfcAndDateWiseCashFlowData, ProjectionCollectionData, NbfcWiseCollectionData


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
    def get_collection_and_loan_booked(nbfc: str, due_date: date) -> [float, float]:
        """
        helper function to get the collection amount from the models.NbfcAndDateWiseCashFlowData filtered
        against the nbfc name and the due_date
        :param nbfc: a string holding the nbfc name
        :param due_date: a string holding the due date
        :return: collection param and loan_booked returned from the models.NbfcAndDateWiseCashFlowData
        """
        queryset = NbfcAndDateWiseCashFlowData.objects.filter(
            nbfc=nbfc,
            due_date=due_date
        ).first()

        if queryset is None:
            return None, None
        return queryset.collection, queryset.loan_booked

    @staticmethod
    def get_predicted_cash_inflow(nbfc: str, due_date: date) -> float:
        """
        function to return the predicted cash inflow for a particular nbfc and a particular due_date
        :param nbfc : a string value storing the nbfc name
        :param due_date : a string value storing the due date
        :return: predicted cash inflow which is the summation of all the predicted amount from
        models.ProjectionCollectionData
        """
        nbfc_instance = NbfcWiseCollectionData.objects.filter(nbfc=nbfc).first()
        if nbfc_instance is None:
            return 0.0
        nbfc_id = nbfc_instance.id
        amount = ProjectionCollectionData.objects.filter(
            nbfc=nbfc_id,
            due_date=due_date
        ).aggregate(Sum('amount'))['amount__sum']
        if amount is None:
            return 0.0
        return amount

    @staticmethod
    def get_variance_and_carry_forward(predicted_cash_inflow: float, collection: float,
                                       capital_inflow: float, hold_cash: float,
                                       loan_booked: float) -> [float, float, float]:
        """
        :param predicted_cash_inflow: float value for predicted_cash_inflow
        :param collection:  float value for collection
        :param capital_inflow: float value for capital_inflow
        :param hold_cash: float value for hold_cash
        :param loan_booked: float value for loan_booked
        :return: variance, carry_forward and available cash flow calculated from given params
        """
        variance = 0
        if predicted_cash_inflow and predicted_cash_inflow != 0:
            variance = ((predicted_cash_inflow - collection) / predicted_cash_inflow) / 100
        carry_forward = (collection + capital_inflow) * (1 - (hold_cash / 100)) + loan_booked
        return variance, carry_forward

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
        return available_cash_flow
