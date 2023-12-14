from rest_framework import serializers
from cash_flow.models import NBFCEligibilityCashFlowHead


class NBFCEligibilityCashFlowHeadSerializer(serializers.ModelSerializer):
    """
    serializer for models.NBFCEligibilityCashFlowHead
    """
    class Meta:
        model = NBFCEligibilityCashFlowHead
        fields = '__all__'
