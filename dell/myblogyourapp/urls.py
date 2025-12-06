from django.urls import path
from myblogyourapp.views import ArticleContentListAPIView
from myblogyourapp.views import ArticleTagContentListAPIView

urlpatterns = [
    path('article-page-content/', ArticleContentListAPIView.as_view(), name='article-page-content'),
    path('article-tag-content/', ArticleTagContentListAPIView.as_view(), name='article-tag-content'),
]