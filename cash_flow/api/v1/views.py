from datetime import datetime, timedelta
from utils.utils import BaseModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from cash_flow.models import (NbfcAndDateWiseCashFlowData,
                              HoldCashData, CapitalInflowData, UserRatioData)
from utils.common_helper import Common


class StoreCapitalInflowView(APIView):
    """
    api view to store the capital inflow against the models.CapitalInflowData
    """
    def post(self, request):
        payload = request.data
        nbfc = payload.get('nbfc', None)
        capital_inflow = payload.get('capital_inflow', None)
        due_date = payload.get('due_date', None)
        if due_date is None:
            due_date = datetime.now()
        else:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        nbfc_and_date_wise_cash_flow_instance = NbfcAndDateWiseCashFlowData.objects.filter(
            nbfc=nbfc,
            due_date=due_date
        ).order_by('-created_at').first()
        if nbfc_and_date_wise_cash_flow_instance is None:
            nbfc_and_date_wise_cash_flow_instance = NbfcAndDateWiseCashFlowData.objects.create(
                nbfc=nbfc,
                due_date=due_date
            )

        end_date = due_date
        set_for_future_flag = payload.get('set_for_future_flag', False)
        if set_for_future_flag is True:
            end_date = payload.get('end_date')
        capital_inflow_instance = CapitalInflowData(
            nbfc=nbfc_and_date_wise_cash_flow_instance,
            start_date=due_date,
            end_date=end_date,
            capital_inflow=capital_inflow,

        )
        capital_inflow_instance.save()
        return Response({"message": "capital inflow stored successfully"}, status=status.HTTP_200_OK)


class StoreHoldCashView(APIView):
    """
    api view to store the hold cash in models.HoldCashData
    """
    def post(self, request):
        payload = request.data
        nbfc = payload.get('nbfc', None)
        hold_cash = payload.get('hold_cash', None)
        due_date = payload.get('due_date', None)
        if due_date is None:
            due_date = datetime.now()
        else:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        nbfc_and_date_wise_cash_flow_instance = NbfcAndDateWiseCashFlowData.objects.filter(
                nbfc=nbfc,
                due_date=due_date
            ).order_by('-created_at').first()
        if nbfc_and_date_wise_cash_flow_instance is None:
            nbfc_and_date_wise_cash_flow_instance = NbfcAndDateWiseCashFlowData.objects.create(
                nbfc=nbfc,
                due_date=due_date
            )

        end_date = due_date
        set_for_future_flag = payload.get('set_for_future_flag', False)
        if set_for_future_flag is True:
            end_date = payload.get('end_date')
        hold_cash_instance = HoldCashData(
            nbfc=nbfc_and_date_wise_cash_flow_instance,
            start_date=due_date,
            end_date=end_date,
            hold_cash=hold_cash,

        )
        hold_cash_instance.save()
        return Response({"message": "hold cash stored successfully"}, status=status.HTTP_200_OK)


class StoreUserRatio(APIView):
    """
    api view to store the user ratio in models.UserRatioData
    """
    def post(self, request):
        payload = request.data
        nbfc = payload.get('nbfc', None)
        due_date = payload.get('due_date', None)
        if due_date is None:
            due_date = datetime.now()
        else:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        old_percentage = payload.get('old_percentage', None)
        new_percentage = 100 - float(old_percentage)

        nbfc_and_date_wise_cash_flow_instance = NbfcAndDateWiseCashFlowData.objects.filter(
            nbfc=nbfc,
            due_date=due_date
        ).first()
        if nbfc_and_date_wise_cash_flow_instance is None:
            nbfc_and_date_wise_cash_flow_instance = NbfcAndDateWiseCashFlowData.objects.create(
                nbfc=nbfc,
                due_date=due_date
            )

        end_date = due_date
        set_for_future_flag = payload.get('set_for_future_flag', False)
        if set_for_future_flag is True:
            end_date = payload.get('end_date')
        user_ratio_instance = UserRatioData(
            nbfc=nbfc_and_date_wise_cash_flow_instance,
            start_date=due_date,
            end_date=end_date,
            new_percentage=float(new_percentage),
            old_percentage=float(old_percentage)
        )
        user_ratio_instance.save()
        return Response({"message": "User ratio stored successfully"}, status=status.HTTP_200_OK)


class StoreCashFlowView(BaseModelViewSet):
    """
    api view to store cash_flow data in models.NbfcAndDateWiseCashFlowData
    """
    def post(self, request):
        payload = request.data
        nbfc = payload['nbfc']
        if nbfc is None:
            return Response({"error: nbfc field is required"}, status=status.HTTP_400_BAD_REQUEST)
        due_date = payload.get('due_date', None)
        if due_date is None:
            due_date = datetime.now()
        else:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")  # Convert string to datetime
        collection = Common.get_collection_and_loan_booked(nbfc, due_date)[0]
        loan_booked = Common.get_collection_and_loan_booked(nbfc, due_date)[1]
        collection = 25000.00
        loan_booked = 16000.0
        if collection is None or loan_booked is None:
            return Response({"error": "could not fetch the collection param or loan_booked param"},
                            status=status.HTTP_404_NOT_FOUND)

        predicted_cash_inflow = Common.get_predicted_cash_inflow(nbfc, due_date)
        capital_inflow = CapitalInflowData.objects.filter(
            nbfc__nbfc=nbfc,
            end_date__gte=due_date,
            start_date__lte=due_date
        ).order_by('-end_date').first().capital_inflow
        hold_cash = HoldCashData.objects.filter(
            nbfc__nbfc=nbfc,
            end_date__gte=due_date,
            start_date__lte=due_date
        ).order_by('-end_date').first().hold_cash

        variance, carry_forward = Common.get_variance_and_carry_forward(
            predicted_cash_inflow=predicted_cash_inflow,
            collection=collection,
            capital_inflow=capital_inflow,
            hold_cash=hold_cash,
            loan_booked=loan_booked
        )
        prev_day_instance = NbfcAndDateWiseCashFlowData.objects.filter(
            nbfc=nbfc,
            due_date=due_date - timedelta(days=1)
        ).first()

        prev_day_carry_forward = 0
        if prev_day_instance is not None:
            prev_day_carry_forward = prev_day_instance.carry_forward
        available_cash_flow = Common.get_available_cash_flow(predicted_cash_inflow, prev_day_carry_forward,
                                                             capital_inflow, hold_cash)
        NbfcAndDateWiseCashFlowData.objects.create(
            nbfc=nbfc,
            due_date=due_date,
            predicted_cash_inflow=predicted_cash_inflow,
            collection=collection,
            carry_forward=carry_forward,
            available_cash_flow=available_cash_flow,
            loan_booked=loan_booked,
            variance=variance,
        )

        return Response({'message': 'NBFC and Date wise cash flow data stored successfully'},
                        status=status.HTTP_200_OK)


class GetCashFlowView(BaseModelViewSet):
    """
    api view for getting the cash flow data from db to be passed on to front_end
    """
    def get(self, request):
        payload = request.data
        nbfc = payload['nbfc']
        if nbfc is None:
            return Response({"error": "nbfc name is required here"}, status=status.HTTP_400_BAD_REQUEST)
        due_date = payload.get('due_date', None)
        if due_date is None:
            due_date = datetime.now()
        else:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")  # Convert string to datetime

        model_instance = NbfcAndDateWiseCashFlowData.objects.filter(nbfc=nbfc, due_date=due_date).first()
        prev_day_instance = NbfcAndDateWiseCashFlowData.objects.filter(
            nbfc=nbfc,
            due_date=due_date - timedelta(days=1)
        ).first()

        prev_day_carry_forward = 0
        if prev_day_instance is not None:
            prev_day_carry_forward = prev_day_instance.carry_forward

        if model_instance is None:
            return Response({"error": "couldn't find any related data"}, status=status.HTTP_404_NOT_FOUND)

        response_dict = {
            'predicted_cash_flow': model_instance.predicted_cash_inflow,
            'collection': model_instance.collection,
            'carry_forward': prev_day_carry_forward,
            'available_cash_flow': model_instance.available_cash_flow,
            'loan_booked': model_instance.loan_booked,
            'variance': model_instance.variance
        }

        return Response(response_dict, status=status.HTTP_200_OK)
