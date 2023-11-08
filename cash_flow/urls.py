from django.urls import path, include

urlpatterns = [
    path('api/', include('cash_flow.api.urls'))
]