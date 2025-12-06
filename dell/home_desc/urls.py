from django.urls import path, include
from rest_framework.routers import DefaultRouter
from home_desc.views import FeatureViewSet

router = DefaultRouter()
router.register('features', FeatureViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]