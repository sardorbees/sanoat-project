from rest_framework import serializers
from .models import IconTitle

class IconTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = IconTitle
        fields = "__all__"
