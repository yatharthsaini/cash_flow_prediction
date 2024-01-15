import requests
import os
from rest_framework import authentication
from django.conf import settings
from cash_flow.models import UserPermissionModel
from rest_framework import exceptions


class CustomAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        url = settings.TOKEN_AUTHENTICATION_URL
        headers = request.META
        req_headers = {
            'User-Agent': headers.get('HTTP_USER_AGENT', ''),
            'Authorization': headers.get('HTTP_AUTHORIZATION', ''),
        }
        response = requests.post(url, headers=req_headers)
        status_code = response.status_code
        if status_code == 200:
            data = response.json()['data']
            user_id = data['user_id']
            if UserPermissionModel.objects.filter(user_id=user_id).exists():
                return None, None
            raise exceptions.PermissionDenied("You do not have permission to access this resource.")
        elif status_code == 401:
            raise exceptions.AuthenticationFailed('Invalid  TOKEN')
        error = response.reason
        raise exceptions.ValidationError({'error': error, 'message': "Something Went Wrong"})
