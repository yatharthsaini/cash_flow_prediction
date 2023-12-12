from rest_framework import generics


class BasModelViewSet(generics.GenericAPIView):
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    class Meta:
        abstract = True
        