from django.urls import path
from cash_flow.api.v1.views import (CapitalInflowDataView, HoldCashDataView, UserRatioDataView,
                                    GetCashFlowView, NBFCBranchView, BookNBFCView, NBFCEligibilityViewSet)

urlpatterns = [
    path('capital-inflow/', CapitalInflowDataView.as_view(), name='capital_inflow'),
    path('hold-cash/', HoldCashDataView.as_view(), name='hold_cash'),
    path('user-ratio/', UserRatioDataView.as_view(), name='user_ratio'),
    path('get-cash-flow/', GetCashFlowView.as_view(), name='get_cash_flow'),
    path('nbfc-branch/', NBFCBranchView.as_view(), name='nbfc_branch'),
    path('book-nbfc/', BookNBFCView.as_view(), name='book_nbfc'),
    path('nbfc-eligibility/<int:pk>/', NBFCEligibilityViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}),
         name='nbfc_eligibility_detail'),
    path('nbfc-eligibility/', NBFCEligibilityViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='nbfc_eligibility')
]
