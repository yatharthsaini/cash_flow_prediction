import os
from datetime import datetime

from rest_framework.permissions import AllowAny

from utils.utils import BaseModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from cash_flow.models import (HoldCashData, CapitalInflowData, UserRatioData, NbfcBranchMaster)
from utils.common_helper import Common


class NBFCBranchView(APIView):

    def post(self, request):
        """
        post api for storing a new nbfc into branch master as a new nbfc registered
        :param request: branch_name contains the name of nbfc to be stored in the branch master
        """
        payload = request.data
        branch_name = payload.get('branch_name', None)
        id = payload.get('id', None)
        delay_in_disbursal = payload.get('delay_in_disbursal', None)
        if id is None:
            return Response({"error": "branch id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if branch_name is None or len(branch_name.strip()) == 0:
            return Response({"error": "branch name is required"}, status=status.HTTP_400_BAD_REQUEST)
        branch_master_instance = NbfcBranchMaster(
            id=id,
            branch_name=branch_name,
        )
        if delay_in_disbursal:
            branch_master_instance.delay_in_disbursal = delay_in_disbursal

        branch_master_instance.save()
        return Response({"message": "NBFC stored to branch master successfully"}, status=status.HTTP_200_OK)

    def get(self, request):
        """
        api for getting the list of registered NBFC's in the branch master
        :param request: nothing to be passed into params
        :return: the list of the registered NBFC's in the branch master with corresponding ids
        """
        queryset = NbfcBranchMaster.objects.all()
        nbfc_dict = dict(queryset.values_list('branch_name', 'id'))

        return Response({'data': nbfc_dict}, status=status.HTTP_200_OK)


class CapitalInflowDataView(APIView):

    def post(self, request):
        """
        api view to store the capital inflow against the models.CapitalInflowData
        """
        payload = request.data
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None:
            return Response({"error": "NBFC is required"}, status=status.HTTP_400_BAD_REQUEST)
        capital_inflow = payload.get('capital_inflow', None)
        due_date = payload.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        else:
            due_date = datetime.now()
        end_date = due_date
        set_for_future_flag = payload.get('set_for_future_flag', False)
        if set_for_future_flag is True:
            end_date = payload.get('end_date', None)
            if end_date:
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
                if end_date < due_date:
                    return Response({"error": "end_date can only be greater than equal to the start_date"},
                                    status=status.HTTP_400_BAD_REQUEST)

        master_instance = NbfcBranchMaster.objects.filter(id=nbfc_id).first()
        if master_instance is None:
            return Response({"error": "NBFC not registered to branch master"}, status=status.HTTP_404_NOT_FOUND)

        capital_inflow_instance = CapitalInflowData.objects.filter(
            nbfc_id=nbfc_id,
            start_date=due_date
        ).first()
        if capital_inflow_instance:
            capital_inflow_instance.end_date = end_date
            capital_inflow_instance.capital_inflow = capital_inflow
            capital_inflow_instance.save()
            return Response({"message": "capital inflow updated successfully"}, status=status.HTTP_200_OK)
        else:
            capital_inflow_instance = CapitalInflowData(
                nbfc=master_instance,
                start_date=due_date,
                end_date=end_date,
                capital_inflow=capital_inflow
            )
            capital_inflow_instance.save()
            return Response({"message": "capital inflow stored successfully"}, status=status.HTTP_200_OK)

    def get(self, request):
        """
        get request for getting capital inflow data for a particular nbfc_id and due_date
        :param request: payload containing nbfc_id and due_date
        """
        payload = request.data
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None:
            return Response({"error": "NBFC is required"}, status=status.HTTP_400_BAD_REQUEST)
        due_date = payload.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        else:
            due_date = datetime.now()

        capital_inflow_instance = CapitalInflowData.objects.filter(nbfc_id=nbfc_id,
                                                                   start_date__lte=due_date,
                                                                   end_date__gte=due_date).first()
        if not capital_inflow_instance:
            return Response({"error": "capital inflow data not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'nbfc_id': capital_inflow_instance.nbfc_id,
            'start_date': capital_inflow_instance.start_date,
            'end_date': capital_inflow_instance.end_date,
            'capital_inflow': capital_inflow_instance.capital_inflow
        }, status=status.HTTP_200_OK)


class HoldCashDataView(APIView):

    def post(self, request):
        """
        api view to store the hold cash in models.HoldCashData
        """
        payload = request.data
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None:
            return Response({"error": "NBFC is required"}, status=status.HTTP_400_BAD_REQUEST)
        hold_cash = payload.get('hold_cash', None)
        due_date = payload.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        else:
            due_date = datetime.now()
        end_date = due_date
        set_for_future_flag = payload.get('set_for_future_flag', False)
        if set_for_future_flag is True:
            end_date = payload.get('end_date', None)
            if end_date:
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
                if end_date < due_date:
                    return Response({"error": "end_date can only be greater than equal to the start_date"},
                                    status=status.HTTP_400_BAD_REQUEST)

        master_instance = NbfcBranchMaster.objects.filter(id=nbfc_id).first()
        if master_instance is None:
            return Response({"error": "NBFC not registered to branch master"}, status=status.HTTP_404_NOT_FOUND)
        hold_cash_instance = HoldCashData.objects.filter(
            nbfc_id=nbfc_id,
            start_date=due_date
        ).first()
        if hold_cash_instance:
            hold_cash_instance.end_date = end_date
            hold_cash_instance.hold_cash = hold_cash
            hold_cash_instance.save()
            return Response({"message": "hold cash updated successfully"}, status=status.HTTP_200_OK)
        else:
            hold_cash_instance = HoldCashData(
                nbfc=master_instance,
                start_date=due_date,
                end_date=end_date,
                hold_cash=hold_cash,
            )
            hold_cash_instance.save()
            return Response({"message": "hold cash stored successfully"}, status=status.HTTP_200_OK)

    def get(self, request):
        """
        get request for getting hold cash data for a particular nbfc_id and due_date
        :param request: payload containing nbfc_id and due_date
        """
        payload = request.data
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None:
            return Response({"error": "NBFC is required"}, status=status.HTTP_400_BAD_REQUEST)
        due_date = payload.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        else:
            due_date = datetime.now()

        hold_cash_instance = HoldCashData.objects.filter(nbfc_id=nbfc_id,
                                                         start_date__lte=due_date,
                                                         end_date__gte=due_date).first()
        if not hold_cash_instance:
            return Response({"error": "hold cash data not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'nbfc_id': hold_cash_instance.nbfc_id,
            'start_date': hold_cash_instance.start_date,
            'end_date': hold_cash_instance.end_date,
            'hold_cash': hold_cash_instance.hold_cash
        }, status=status.HTTP_200_OK)


class UserRatioDataView(APIView):

    def post(self, request):
        """
        api view to store the user ratio in models.UserRatioData
        """
        payload = request.data
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None:
            return Response({"error": "NBFC is required"}, status=status.HTTP_400_BAD_REQUEST)
        old_percentage = payload.get('old_percentage', None)
        new_percentage = 100 - float(old_percentage)
        due_date = payload.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        else:
            due_date = datetime.now()
        end_date = due_date
        set_for_future_flag = payload.get('set_for_future_flag', False)
        if set_for_future_flag is True:
            end_date = payload.get('end_date', None)
            if end_date:
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
                if end_date < due_date:
                    return Response({"error": "end_date can only be greater than equal to the start_date"},
                                    status=status.HTTP_400_BAD_REQUEST)

        master_instance = NbfcBranchMaster.objects.filter(id=nbfc_id).first()
        if master_instance is None:
            return Response({"error": "NBFC not registered to branch master"}, status=status.HTTP_404_NOT_FOUND)
        user_ratio_instance = UserRatioData.objects.filter(
            nbfc_id=nbfc_id,
            start_date=end_date
        ).first()
        if user_ratio_instance:
            user_ratio_instance.end_date = end_date
            user_ratio_instance.old_percentage = old_percentage
            user_ratio_instance.new_percentage = new_percentage
            user_ratio_instance.save()
            return Response({"message": "user ratio data updated successfully"}, status=status.HTTP_200_OK)
        else:
            user_ratio_instance = UserRatioData(
                nbfc=master_instance,
                start_date=due_date,
                end_date=end_date,
                new_percentage=float(new_percentage),
                old_percentage=float(old_percentage)
            )
            user_ratio_instance.save()
            return Response({"message": "User ratio stored successfully"}, status=status.HTTP_200_OK)

    def get(self, request):
        """
        get request for getting user ratio data for a particular nbfc_id and due_date
        :param request: payload containing nbfc_id and due_date
        """
        payload = request.data
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None:
            return Response({"error": "NBFC is required"}, status=status.HTTP_400_BAD_REQUEST)
        due_date = payload.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        else:
            due_date = datetime.now()

        user_ratio_instance = UserRatioData.objects.filter(nbfc_id=nbfc_id,
                                                           start_date__lte=due_date,
                                                           end_date__gte=due_date).first()
        if not user_ratio_instance:
            return Response({"error": "user ratio data not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'nbfc_id': user_ratio_instance.nbfc_id,
            'start_date': user_ratio_instance.start_date,
            'end_date': user_ratio_instance.end_date,
            'old_user_percentage': user_ratio_instance.old_percentage,
            'new_user_percentage': user_ratio_instance.new_percentage
        }, status=status.HTTP_200_OK)


class GetCashFlowView(BaseModelViewSet):
    """
    api view for getting the cash flow data from db to be passed on to front-end
    real time fields are to be returned in real time that are : collection, loan_booked, carry_forward,
    available_cash_flow and variance
    static fields to be returned that are: capital_inflow, hold_cash, and user_ratio
    payload contains : nbfc in the form of nbfc_id and a due_date
    """

    def get(self, request):
        payload = request.data
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None:
            return Response({"error": "NBFC is required"}, status=status.HTTP_400_BAD_REQUEST)
        due_date = payload.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        else:
            due_date = datetime.now()
        master_instance = NbfcBranchMaster.objects.filter(id=nbfc_id).first()
        if master_instance is None:
            return Response({"error": "NBFC not registered to branch master"}, status=status.HTTP_404_NOT_FOUND)

        predicted_cash_inflow = Common.get_predicted_cash_inflow(nbfc_id, due_date)
        collection, loan_booked = Common.get_collection_and_loan_booked(nbfc_id, due_date)

        capital_inflow = 0.0
        capital_inflow_instance = CapitalInflowData.objects.filter(nbfc_id=nbfc_id,
                                                                   start_date__lte=due_date,
                                                                   end_date__gte=due_date).first()
        if capital_inflow_instance:
            capital_inflow = capital_inflow_instance.capital_inflow

        hold_cash = 0.0
        hold_cash_instance = HoldCashData.objects.filter(nbfc_id=nbfc_id,
                                                         start_date__lte=due_date,
                                                         end_date__gte=due_date).first()
        if hold_cash_instance:
            hold_cash = hold_cash_instance.hold_cash

        old_user_percentage = 0.0
        new_user_percentage = 0.0
        user_ratio_instance = UserRatioData.objects.filter(nbfc_id=nbfc_id,
                                                           start_date__lte=due_date,
                                                           end_date__gte=due_date).first()
        if user_ratio_instance:
            old_user_percentage = user_ratio_instance.old_percentage
            new_user_percentage = user_ratio_instance.new_percentage

        carry_forward = Common.get_carry_forward(collection, capital_inflow, hold_cash, loan_booked)
        prev_day_carry_forward = Common.get_prev_day_carry_forward(nbfc_id, due_date)
        available_cash_flow = Common.get_available_cash_flow(predicted_cash_inflow, prev_day_carry_forward,
                                                             capital_inflow, hold_cash)
        variance = Common.get_real_time_variance(predicted_cash_inflow, collection)

        return Response({
            'predicted_cash_inflow': predicted_cash_inflow,
            'collection': collection,
            'carry_forward': carry_forward,
            'capital_inflow': capital_inflow,
            'hold_cash': hold_cash,
            'loan_booked': loan_booked,
            'available_cash_flow': available_cash_flow,
            'variance': variance,
            'old_user_percentage': old_user_percentage,
            'new_user_percentage': new_user_percentage
        }, status=status.HTTP_200_OK)


class SuccessStatus(APIView):
    """
    success status api
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "status": "Success",
                "ip_address": os.environ.get("PRIVATE_IP_ADDRESS"),
                "server_node": os.environ.get("SERVER_NODE"),
            },
            status=status.HTTP_200_OK,
        )
