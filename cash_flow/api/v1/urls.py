from django.urls import path
from cash_flow.api.v1.views import (CapitalInflowDataView, HoldCashDataView, UserRatioDataView,
                                    GetCashFlowView, NBFCBranchView, BookNBFCView, NBFCEligibilityViewSet,
                                    CreatePredictionData, ExportBookingAmount, CreateUserPermission)

urlpatterns = [
    path('capital-inflow/', CapitalInflowDataView.as_view(), name='capital_inflow'),
    path('hold-cash/', HoldCashDataView.as_view(), name='hold_cash'),
    path('user-ratio/', UserRatioDataView.as_view(), name='user_ratio'),
    path('get-cash-flow/', GetCashFlowView.as_view(), name='get_cash_flow'),
    path('nbfc-branch/', NBFCBranchView.as_view(), name='nbfc_branch'),
    path('book-nbfc/', BookNBFCView.as_view(), name='book_nbfc'),
    path('nbfc-eligibility/<int:pk>/', NBFCEligibilityViewSet.as_view({'patch': 'partial_update'}),
         name='nbfc_eligibility_detail'),
    path('nbfc-eligibility/', NBFCEligibilityViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='nbfc_eligibility'),
    path('create-prediction-data/', CreatePredictionData.as_view(), name='create-prediction-data'),
    path('export-booking-amount/', ExportBookingAmount.as_view(), name='export-booking-amount'),
    path('create-user-permission/', CreateUserPermission.as_view(), name='create-user-permission'),
]
