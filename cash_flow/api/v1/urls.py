from django.urls import path
from cash_flow.api.v1.views import (CapitalInflowDataView, HoldCashDataView, UserRatioDataView,
                                    GetCashFlowView, NBFCBranchView)

urlpatterns = [
    path('capital-inflow/', CapitalInflowDataView.as_view(), name='capital_inflow'),
    path('hold-cash/', HoldCashDataView.as_view(), name='hold_cash'),
    path('user-ratio/', UserRatioDataView.as_view(), name='user_ratio'),
    path('get-cash-flow/', GetCashFlowView.as_view(), name='get_cash_flow'),
    path('nbfc-branch/', NBFCBranchView.as_view(), name='nbfc_branch'),
]
