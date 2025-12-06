from rest_framework import serializers
from .models import IndustryArticle

class IndustryArticleSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = IndustryArticle
        fields = [
            "id", "title", "subtitle", "content",
            "year", "statistic", "image", "image_url",
            "created_at", "updated_at"
        ]
        read_only_fields = ("created_at", "updated_at")

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        if obj.image:
            return obj.image.url
        return None
