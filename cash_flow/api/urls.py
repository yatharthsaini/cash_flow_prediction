from django.urls import path, include

urlpatterns = [
    path('v1/', include('cash_flow.api.v1.urls'))
]