from rest_framework import serializers
from myblogyourapp.models import Article
from myblogyourapp.models import ArticleTag


class ArticleContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = "__all__"
        read_only_fields = [fields]


class ArticleTagContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleTag
        fields = "__all__"
        read_only_fields = [fields]
