from django.urls import path
from cash_flow.api.v1.views import (StoreCapitalInflowView, StoreHoldCashView, StoreUserRatio,
                                    StoreCashFlowView, GetCashFlowView)

urlpatterns = [
    path('store-capital-inflow/', StoreCapitalInflowView.as_view(), name='store_capital_inflow'),
    path('store-hold-cash/', StoreHoldCashView.as_view(), name='store_hold_cash'),
    path('store-user-ratio/', StoreUserRatio.as_view(), name='store_user_ratio'),
    path('store-cash-flow/', StoreCashFlowView.as_view(), name='store_cash_flow'),
    path('get-cash-flow/', GetCashFlowView.as_view(), name='get_cash_flow'),
]
