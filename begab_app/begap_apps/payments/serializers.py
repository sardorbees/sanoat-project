from rest_framework import serializers
from .models import PaymentMethod

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = (
            'id',
            'type',
            'title',
            'masked_number',
            'is_default',
        )
