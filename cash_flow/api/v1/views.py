import os
from datetime import datetime, timedelta
from django.core.cache import cache

from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet
from utils.utils import BaseModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from cash_flow.models import (HoldCashData, CapitalInflowData, UserRatioData, NbfcBranchMaster,
                              NBFCEligibilityCashFlowHead)
from cash_flow.serializers import NBFCEligibilityCashFlowHeadSerializer
from cash_flow.external_calls import get_cash_flow_data
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
        payload = request.query_params
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None or nbfc_id == '':
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
        payload = request.query_params
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None or nbfc_id == '':
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
        payload = request.query_params
        nbfc_id = payload.get('nbfc_id', None)
        if nbfc_id is None or nbfc_id == '':
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

        predicted_cash_inflow = Common.get_predicted_cash_inflow(nbfc_id, due_date)

        # cache check for loan booked param
        loan_booked_key = f"loan_booked_{nbfc_id}_{due_date}"
        cached_loan_booked = cache.get(loan_booked_key)

        if cached_loan_booked is not None:
            loan_booked = cached_loan_booked
        else:
            loan_booked = Common.get_collection_and_loan_booked(nbfc_id, due_date)[1]
            cache.set(loan_booked_key, loan_booked, timeout=60 * 60 * 24)

        collection = Common.get_collection_and_loan_booked(nbfc_id, due_date)[0]

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

        # by default taking old user percentage as 100 and new user percentage as 0 if user ratio data not present
        old_user_percentage = 100.0
        new_user_percentage = 0.0
        user_ratio_instance = UserRatioData.objects.filter(nbfc_id=nbfc_id,
                                                           start_date__lte=due_date,
                                                           end_date__gte=due_date).first()
        if user_ratio_instance:
            old_user_percentage = user_ratio_instance.old_percentage
            new_user_percentage = user_ratio_instance.new_percentage

        carry_forward = Common.get_carry_forward(collection, capital_inflow, hold_cash, loan_booked)
        prev_day_carry_forward = Common.get_prev_day_carry_forward(nbfc_id, due_date)

        # cache check for available_cash_flow
        available_cash_flow_key = f"available_cash_flow_{nbfc_id}_{due_date}"
        cached_available_cash_flow = cache.get(available_cash_flow_key)

        if cached_available_cash_flow is not None:
            # Use cached value if available
            available_cash_flow = cached_available_cash_flow
        else:
            # Calculate and store in cache
            available_cash_flow = Common.get_available_cash_flow(
                predicted_cash_inflow, prev_day_carry_forward, capital_inflow, hold_cash
            )
            cache.set(available_cash_flow_key, available_cash_flow, timeout=60 * 60 * 24)
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


class BookNBFCView(APIView):

    def get(self, request):
        """
        :param request: will contain the user_id, loan_type, cibil_score, loan_tenure, loan_amount, loan_tenure, unit,
        assigned_nbfc_id, old_user
        :return: the nbfc_id to be booked for the loan
        """
        payload = request.data
        user_id = payload.get('user_id', None)
        loan_type = payload.get('loan_type', None)
        old_user = payload.get('old_user', True)
        assigned_nbfc_id = payload.get('old_nbfc_id', None)
        cibil_score = payload.get('cibil_score', None)
        loan_tenure = payload.get('loan_tenure', None)
        loan_tenure_unit = payload.get('loan_tenure_unit', None)
        loan_amount = payload.get('loan_amount', None)
        # checking if due_date not present then taking current date
        due_date = payload.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        else:
            due_date = datetime.now()

        # missing fields check
        if user_id is None or loan_type is None or cibil_score is None or loan_tenure is None or loan_amount is None \
                or loan_tenure_unit is None:
            return Response({'error': 'one of the fields is missing'}, status=status.HTTP_400_BAD_REQUEST)

        # case when a user has already assigned nbfc
        if assigned_nbfc_id:
            if str(assigned_nbfc_id) in settings.NO_CHANGE_NBFC_LIST:
                """
                nbfc will not be changed if already assigned for some cases like Unity Bank
                """
                return Response({
                    'data': {
                        'user_id': user_id,
                        'assigned_nbfc': assigned_nbfc_id
                    },
                    'message': 'No change in  nbfc is required because assigned nbfc is listed in no-update nbfc list'
                }, status=status.HTTP_200_OK)

            hold_cash = 0.0
            hold_cash_instance = HoldCashData.objects.filter(nbfc_id=assigned_nbfc_id,
                                                             start_date__lte=due_date,
                                                             end_date__gte=due_date).first()
            if hold_cash_instance:
                hold_cash = hold_cash_instance.hold_cash
            if hold_cash == 100:
                return Response({
                    'data': {
                        'user_id': user_id,
                        'assigned_nbfc': assigned_nbfc_id
                    },
                    'message': 'No change in nbfc is required because of 100 percent hold cash of assigned nbfc'
                }, status=status.HTTP_200_OK)

            str_due_date = due_date.strftime('%Y-%m-%d')
            cash_flow_data = get_cash_flow_data(assigned_nbfc_id, str_due_date).json()
            available_credit_line = cash_flow_data.get('available_cash_flow', None)
            if available_credit_line >= loan_amount:
                return Response({
                    'data': {
                        'user_id': user_id,
                        "assigned_nbfc": assigned_nbfc_id
                    },
                    'message': 'no change in nbfc is required because of already available credit line with the '
                               'assigned nbfc'
                }, status=status.HTTP_200_OK)

        if loan_tenure_unit == 'days':
            loan_tenure = timedelta(loan_tenure)
        elif loan_tenure_unit == 'months':
            loan_tenure = timedelta(loan_tenure * 30)  # Assuming an average of 30 days in a month
        elif loan_tenure_unit == 'years':
            loan_tenure = timedelta(loan_tenure * 365)  # Assuming 365 days in a year

        eligibility_queryset = NBFCEligibilityCashFlowHead.objects.filter(
            loan_type=loan_type,
            min_cibil_score__lte=cibil_score,
            min_loan_tenure__lte=loan_tenure,
            max_loan_tenure__gte=loan_tenure,
            min_loan_amount__lte=loan_amount,
            max_loan_amount__gte=loan_amount,
            should_check=True
        )

        eligible_branches_list = list(eligibility_queryset.values('nbfc').distinct())
        eligible_branches_list = [item['nbfc'] for item in eligible_branches_list]

        if len(eligible_branches_list) == 0:
            return Response({"message": "No branch is eligible for nbfc updation"},
                            status=status.HTTP_404_NOT_FOUND)

        common_instance = Common()
        updated_nbfc_id = common_instance.get_nbfc_for_loan_to_be_booked(branches_list=eligible_branches_list,
                                                                         old_user=old_user,
                                                                         sanctioned_amount=loan_amount)

        if updated_nbfc_id == -1:
            return Response({'error': 'something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'data': {
                'user_id': user_id,
                'assigned_nbfc': assigned_nbfc_id,
                'updated_nbfc_id': updated_nbfc_id,
            },
            'message': 'nbfc is updated for the user'
        }, status=status.HTTP_200_OK)


class NBFCEligibilityViewSet(ModelViewSet):
    """
    Base Model for serializers.NBFCEligibilityCashFlowHeadSerializer which is further inherited from
    models.NBFCEligibilityCashFlowHead
    """
    serializer_class = NBFCEligibilityCashFlowHeadSerializer
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
