from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IndustryArticleViewSet

router = DefaultRouter()
router.register(r"articles", IndustryArticleViewSet, basename="industry-article")

urlpatterns = [
    path("", include(router.urls)),
]
