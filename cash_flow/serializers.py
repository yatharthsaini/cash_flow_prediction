from rest_framework import serializers

from cash_flow.models import NBFCEligibilityCashFlowHead, UserPermissionModel


class NBFCEligibilityCashFlowHeadSerializer(serializers.ModelSerializer):
    """
    serializer for models.NBFCEligibilityCashFlowHead
    """
    class Meta:
        model = NBFCEligibilityCashFlowHead
        fields = '__all__'


class UserPermissionModelSerializer(serializers.ModelSerializer):
    """
    serializer for models.UserPermissionModel
    """
    class Meta:
        model = UserPermissionModel
        fields = '__all__'
        extra_kwargs = {
            'user_id': {'required': True},
            'email': {'required': True}
        }
