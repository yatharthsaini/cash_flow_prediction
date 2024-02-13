import os
import pandas as pd
import base64
from datetime import datetime

from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet
from utils.utils import BaseModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.core.cache import cache
from django.db.models import Sum

from cash_flow.models import (HoldCashData, CapitalInflowData, UserRatioData, NbfcBranchMaster,
                              NBFCEligibilityCashFlowHead, LoanDetail, ProjectionCollectionData,
                              UserPermissionModel)
from cash_flow.serializers import NBFCEligibilityCashFlowHeadSerializer, UserPermissionModelSerializer
from cash_flow.tasks import (populate_available_cash_flow, task_for_loan_booked, populate_json_against_nbfc,
                             task_for_loan_booking, populate_wacm, run_migrate)
from cash_flow.api.v1.authenticator import CustomAuthentication, ServerAuthentication
from utils.common_helper import Common


class NBFCBranchView(APIView):
    authentication_classes = [CustomAuthentication]

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

        try:
            branch_master_instance = NbfcBranchMaster.objects.filter(
                branch_name=branch_name,
                id=id
            ).first()

            if branch_master_instance:
                return Response({'message': 'NBFC already registered to branch master'}, status=status.HTTP_200_OK)

            branch_master_instance = NbfcBranchMaster(
                id=id,
                branch_name=branch_name
            )
            if delay_in_disbursal:
                branch_master_instance.delay_in_disbursal = delay_in_disbursal

            branch_master_instance.save()
            return Response({"message": "NBFC stored to branch master successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            error_message = str(e)
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    authentication_classes = [CustomAuthentication]

    def post(self, request):
        """
        api view to store the capital inflow against the models.CapitalInflowData
        """
        payload = request.data
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None:
            return Response({"error": "nbfc_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        capital_inflow = payload.get('capital_inflow', None)
        if capital_inflow is None:
            return Response({"error": "capital_inflow is required"}, status=status.HTTP_400_BAD_REQUEST)
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

        try:
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
        except Exception as e:
            error_message = str(e)
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """
        get request for getting capital inflow data for a particular nbfc_id and due_date
        :param request: payload containing nbfc_id and due_date
        """
        payload = request.query_params
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None or nbfc_id == '':
            return Response({"error": "NBFC is required"}, status=status.HTTP_400_BAD_REQUEST)
        due_date = payload.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        else:
            due_date = datetime.now()

        try:
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
        except Exception as e:
            error_message = str(e)
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HoldCashDataView(APIView):
    authentication_classes = [CustomAuthentication]

    def post(self, request):
        """
        api view to store the hold cash in models.HoldCashData
        """
        payload = request.data
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None:
            return Response({"error": "nbfc_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        hold_cash = payload.get('hold_cash', None)
        if hold_cash is None:
            return Response({"error": "hold_cash is required"}, status=status.HTTP_400_BAD_REQUEST)
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

        try:
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
        except Exception as e:
            error_message = str(e)
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """
        get request for getting hold cash data for a particular nbfc_id and due_date
        :param request: payload containing nbfc_id and due_date
        """
        payload = request.query_params
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None or nbfc_id == '':
            return Response({"error": "NBFC is required"}, status=status.HTTP_400_BAD_REQUEST)
        due_date = payload.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        else:
            due_date = datetime.now()

        try:
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
        except Exception as e:
            error_message = str(e)
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserRatioDataView(APIView):
    authentication_classes = [CustomAuthentication]

    def post(self, request):
        """
        api view to store the user ratio in models.UserRatioData
        """
        payload = request.data
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None:
            return Response({"error": "nbfc_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        old_percentage = payload.get('old_percentage', None)
        if old_percentage is None:
            return Response({"error": "old_percentage is required"}, status=status.HTTP_400_BAD_REQUEST)
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

        try:
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
        except Exception as e:
            error_message = str(e)
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """
        get request for getting user ratio data for a particular nbfc_id and due_date
        :param request: payload containing nbfc_id and due_date
        """
        payload = request.query_params
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None or nbfc_id == '':
            return Response({"error": "NBFC is required"}, status=status.HTTP_400_BAD_REQUEST)
        due_date = payload.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        else:
            due_date = datetime.now()

        try:
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
        except Exception as e:
            error_message = str(e)
            return Response({'error', error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetCashFlowView(BaseModelViewSet):
    """
    api view for getting the cash flow data from db to be passed on to front-end
    real time fields are to be returned in real time that are : collection, loan_booked, carry_forward,
    available_cash_flow and variance
    static fields to be returned that are: capital_inflow, hold_cash, and user_ratio
    payload contains : nbfc in the form of nbfc_id and a due_date
    """
    authentication_classes = [CustomAuthentication]

    def get(self, request):
        payload = request.query_params
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None or nbfc_id == '':
            return Response({"error": "NBFC is required"}, status=status.HTTP_400_BAD_REQUEST)
        due_date = payload.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        else:
            due_date = datetime.now()
        master_instance = NbfcBranchMaster.objects.filter(id=nbfc_id).first()
        if master_instance is None:
            return Response({"error": "NBFC not registered to branch master"}, status=status.HTTP_404_NOT_FOUND)

        try:
            predicted_cash_inflow = Common.get_predicted_cash_inflow(nbfc_id, due_date)

            loan_booked = cache.get('loan_booked', {}).get(nbfc_id, {}).get('total', 0)
            if not loan_booked:
                loan_booked = task_for_loan_booked(nbfc_id)

            collection_data = Common.get_collection_and_last_day_balance(nbfc_id, due_date)
            collection = collection_data[0]
            if collection is None:
                collection = 0
            last_day_balance = collection_data[1]

            capital_inflow = Common.get_nbfc_capital_inflow(due_date, nbfc_id)
            hold_cash = Common.get_hold_cash_value(due_date, nbfc_id)
            user_ratio = Common.get_user_ratio(due_date, nbfc_id)
            old_user_percentage = user_ratio[0]
            new_user_percentage = user_ratio[1]

            available_cash = cache.get('available_balance', {}).get(nbfc_id, {}).get('total')

            if not available_cash:
                available_cash = populate_available_cash_flow(nbfc_id)

            variance = Common.get_real_time_variance(predicted_cash_inflow, collection)

            return Response({
                'predicted_cash_inflow': predicted_cash_inflow,
                'collection': collection,
                'carry_forward': last_day_balance,
                'capital_inflow': capital_inflow,
                'hold_cash': hold_cash,
                'loan_booked': loan_booked,
                'available_cash_flow': available_cash,
                'variance': variance,
                'old_user_percentage': old_user_percentage,
                'new_user_percentage': new_user_percentage
            }, status=status.HTTP_200_OK)
        except Exception as e:
            error_message = str(e)
            return Response({'error', error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SuccessStatus(APIView):
    """
    success status api
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "STATUS": "Success",
                "IP_ADDRESS": os.environ.get("PRIVATE_IP_ADDRESS"),
                "HOSTNAME": os.environ.get("HOSTNAME"),
            },
            status=status.HTTP_200_OK,
        )


class BookNBFCView(APIView):
    authentication_classes = [ServerAuthentication]

    def post(self, request):
        try:
            payload = request.data
            assigned_nbfc = payload.get('assigned_nbfc', None)
            if assigned_nbfc == 27:
                return Response({'message': 'no change in nbfc', 'assigned_nbfc': assigned_nbfc},
                                status=status.HTTP_200_OK)

            required_fields = ['user_id', 'loan_type', 'request_type', 'cibil_score', 'credit_limit']
            for i in required_fields:
                if not payload.get(i):
                    return Response({'error': f'Invalid {i} value'}, status=status.HTTP_400_BAD_REQUEST)

            user_id = payload['user_id']
            loan_type = payload['loan_type']
            request_type = payload['request_type']
            cibil_score = payload['cibil_score']
            credit_limit = payload['credit_limit']

            loan_id = payload.get('loan_id', None)
            user_type = payload.get('user_type', 'O')
            due_date = datetime.now().date()

            amount = payload.get('amount', credit_limit)
            amount = amount if request_type == 'LAD' else credit_limit

            if assigned_nbfc == 5:
                return Response(
                    {'data': {'user_id': user_id, 'assigned_nbfc': assigned_nbfc, 'updated_nbfc': assigned_nbfc}},
                    status=status.HTTP_200_OK)

            common_instance = Common()
            assigned_nbfc, updated_nbfc_id = self.get_nbfc_for_loan_booking(
                assigned_nbfc, user_id, loan_id, user_type, credit_limit, loan_type, request_type, cibil_score, amount,
                due_date, common_instance)

            if assigned_nbfc == updated_nbfc_id:
                return Response(
                    {'data': {'user_id': user_id, 'assigned_nbfc': assigned_nbfc, 'updated_nbfc': updated_nbfc_id}},
                    status=status.HTTP_200_OK)

            return Response(
                {'data': {'user_id': user_id, 'assigned_nbfc': assigned_nbfc, 'updated_nbfc': updated_nbfc_id}},
                status=status.HTTP_200_OK)

        except Exception as e:
            error_message = str(e)
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_nbfc_for_loan_booking(self, assigned_nbfc, user_id, loan_id, user_type, credit_limit, loan_type,
                                  request_type, cibil_score, amount, due_date, common_instance):
        user_loan_status = LoanDetail.objects.filter(user_id=user_id, loan_id=loan_id, is_booked=True).first()

        assigned_nbfc = user_loan_status.nbfc_id if user_loan_status else assigned_nbfc
        # assigned_nbfc line should be removed when we go live in productivity

        user_prev_loan_status = user_loan_status.status if user_loan_status else None
        cached_available_balance = cache.get('available_balance', {})
        if assigned_nbfc:
            available_cash = cached_available_balance.get(assigned_nbfc, {}).get(user_type, 0)
            if available_cash >= amount or user_loan_status:
                self.task_for_loan_booking(credit_limit, user_type, loan_type, user_id, request_type, cibil_score,
                                           assigned_nbfc, loan_id, user_prev_loan_status, amount, user_loan_status)
                return assigned_nbfc, assigned_nbfc

        tenure_days = int(loan_type[1:]) if loan_type.startswith('E') else 45
        eligibility_loan_type = 'E' if loan_type != 'P' else 'P'

        eligibility_queryset = NBFCEligibilityCashFlowHead.objects.filter(
            loan_type=eligibility_loan_type,
            min_cibil_score__lte=cibil_score,
            min_loan_tenure__lte=tenure_days,
            max_loan_tenure__gte=tenure_days,
            min_loan_amount__lte=amount,
            max_loan_amount__gte=amount,
            should_check=True
        )

        eligible_branches_list = list(eligibility_queryset.values_list('nbfc', flat=True))

        eligible_branches_list.append(assigned_nbfc)
        eligible_branches_list = set(cached_available_balance.keys()).intersection(eligible_branches_list)

        updated_nbfc_id = common_instance.get_nbfc_for_loan_to_be_booked(
            branches_list=eligible_branches_list,
            user_type=user_type,
            sanctioned_amount=amount
        )

        if updated_nbfc_id:
            self.task_for_loan_booking(credit_limit, user_type, loan_type, user_id, request_type, cibil_score,
                                       updated_nbfc_id, loan_id, user_prev_loan_status, amount, user_loan_status)

        return assigned_nbfc, updated_nbfc_id

    def task_for_loan_booking(self, credit_limit, user_type, loan_type, user_id, request_type, cibil_score,
                              nbfc_id, loan_id, prev_loan_status, loan_amount, is_booked):
        task_for_loan_booking(
            credit_limit=credit_limit,
            user_type=user_type,
            loan_type=loan_type,
            user_id=user_id,
            request_type=request_type,
            cibil_score=cibil_score,
            nbfc_id=nbfc_id,
            loan_id=loan_id,
            prev_loan_status=prev_loan_status,
            loan_amount=loan_amount,
            is_booked=is_booked
        )


class NBFCEligibilityViewSet(ModelViewSet):
    """
    Base Model for serializers.NBFCEligibilityCashFlowHeadSerializer which is further inherited from
    models.NBFCEligibilityCashFlowHead
    """
    serializer_class = NBFCEligibilityCashFlowHeadSerializer
    authentication_classes = [CustomAuthentication]
    queryset = NBFCEligibilityCashFlowHead.objects.all()
    lookup_field = 'nbfc'

    def list(self, request, *args, **kwargs):
        nbfc_value = request.data.get('nbfc', None)

        if nbfc_value is not None:
            # If nbfc is provided in the payload, filter the queryset
            queryset = self.filter_queryset(self.get_queryset()).filter(nbfc=nbfc_value)
        else:
            # If nbfc is not provided, get all objects
            queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        nbfc = request.data.get('nbfc')
        loan_type = request.data.get('loan_type')

        # Check if an object with the same nbfc and loan_type already exists
        existing_instance = NBFCEligibilityCashFlowHead.objects.filter(nbfc=nbfc, loan_type=loan_type).first()
        if existing_instance:
            serializer = self.get_serializer(existing_instance)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        lookup_value = self.kwargs.get(self.lookup_field)
        queryset = self.filter_queryset(self.get_queryset())
        try:
            obj = queryset.get(**{self.lookup_field: lookup_value})
        except NBFCEligibilityCashFlowHead.DoesNotExist:
            return Response(
                {"detail": f"Object with {self.lookup_field}={lookup_value} does not exist."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreatePredictionData(APIView):
    """
    api view to create the prediction data
    """
    authentication_classes = [CustomAuthentication]

    def post(self, request):
        payload = request.data
        due_date = payload.get('due_date')
        if not due_date:
            return Response({'error': 'Invalid Due Date'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        calculate_projected_amount = payload.get('calculate_projected_amount', False)

        try:
            populate_json_against_nbfc(due_date)
            if calculate_projected_amount:
                populate_wacm(due_date)
        except Exception as e:
            msg = str(e)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Success'}, status=status.HTTP_201_CREATED)


class ExportBookingAmount(APIView):
    """
    api view to export booking amount
    """

    def get(self, request):
        payload = request.query_params
        date = payload.get('date')

        if not date:
            return Response({'error': 'Invalid Date'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        try:
            loans = LoanDetail.objects.filter(updated_at__date=date, is_booked=True).order_by('nbfc_id')
            loans = loans.values('nbfc__branch_name', 'user_type').annotate(
                booking=Sum('amount')
            )
            predicted_cash_inflow = ProjectionCollectionData.objects.filter(collection_date=date).values(
                'nbfc__branch_name', 'new_user_amount', 'old_user_amount')

            df2 = pd.DataFrame(predicted_cash_inflow)

            df = pd.DataFrame(loans)
            if not df.empty:
                col_name = {
                    'nbfc__branch_name': 'NBFC',
                    'user_type': 'User Type',
                    'predicted_amount': 'Predicted Cash Inflow',
                    'booking': 'New Logic Booking',
                }

                if not df2.empty:
                    df = df.merge(df2, how='left', on='nbfc__branch_name')
                else:
                    df['old_user_amount'] = 0
                    df['new_user_amount'] = 0
                df['predicted_amount'] = df.apply(
                    lambda row: row['old_user_amount'] if row['user_type'] == 'O' else
                    row['new_user_amount'], axis=1)
                df.rename(columns=col_name, inplace=True)
                df['Old Logic Booking'] = ''
                df['Date'] = date
                df = df[
                    ['Date', 'NBFC', 'Predicted Cash Inflow', 'User Type', 'Old Logic Booking', 'New Logic Booking']]
                csv_data = df.to_csv(index=False)
                csv_bytes = csv_data.encode('utf-8')
                base64_data = base64.b64encode(csv_bytes).decode('utf-8')

                return Response({'message': 'Success', 'url': 'data:text/csv;base64,' + base64_data})
            return Response({'error': 'No data found'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            msg = str(e)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)


class UserPermissionModelViewSet(ModelViewSet):
    authentication_classes = [CustomAuthentication]
    queryset = UserPermissionModel.objects.all()
    serializer_class = UserPermissionModelSerializer
    lookup_field = 'user_id'

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        if UserPermissionModel.objects.filter(user_id=user_id).exists():
            return Response({'error': 'User with this user_id already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id', None)
        if user_id:
            queryset = UserPermissionModel.objects.filter(user_id=user_id)
        else:
            queryset = UserPermissionModel.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MigrateView(APIView):
    """
    api view to call the celery function for hitting the migrate command from django.core.command
    """
    authentication_classes = [ServerAuthentication]

    def post(self, request):
        payload = request.data
        password = payload.get('password')
        if not password:
            return Response({'error': 'Invalid Password'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        try:
            run_migrate(password)
            return Response({'message': 'Migrations ran successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            msg = str(e)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)


class RealTimeNBFCDetail(APIView):
    """
    api view to get the available balance and loan booked in real time using cache
    """
    authentication_classes = [ServerAuthentication]

    def get(self, request):
        """
        get request which takes the nbfc_id in the query params
        """
        payload = request.query_params
        nbfc_id = payload.get('nbfc_id', None)

        try:
            loan_booked_data = cache.get('loan_booked_data', {})
            available_balance_data = cache.get('available_balance', {})

            if nbfc_id is None or nbfc_id == '':
                return Response(
                    {
                        'data': {
                            'loan_booked': loan_booked_data,
                            'available_balance': available_balance_data
                        }
                    },
                    status=status.HTTP_200_OK
                )

            loan_booked_data = loan_booked_data.get(nbfc_id, {})
            available_balance_data = available_balance_data.get(nbfc_id, {})

            return Response(
                {
                    'data': {
                        'loan_booked': loan_booked_data,
                        'available_balance': available_balance_data
                    }
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            msg = str(e)
            return Response({'error': msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
