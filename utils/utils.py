from rest_framework import generics


class BaseModelViewSet(generics.GenericAPIView):
    """
    base model view set that contains http methods of get, post, patch, delete, options, head
    """
    http_method_names = ['post', 'patch', 'get', 'head', 'delete', 'options']

    class Meta:
        abstract = True
