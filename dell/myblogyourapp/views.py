from rest_framework import generics
from rest_framework.exceptions import NotFound

from myblogyourapp.models import Article
from myblogyourapp.serializers import ArticleContentSerializer
from myblogyourapp.models import ArticleTag
from myblogyourapp.serializers import ArticleTagContentSerializer

class ArticleContentListAPIView(generics.RetrieveAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleContentSerializer

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.first()
        if obj is None:
            raise NotFound(detail="MainPageContent object not found")
        return obj

class ArticleTagContentListAPIView(generics.RetrieveAPIView):
    queryset = ArticleTag.objects.all()
    serializer_class = ArticleTagContentSerializer

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.first()
        if obj is None:
            raise NotFound(detail="MainPageContent object not found")
        return obj
