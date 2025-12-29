from django.urls import path
from .views import ApplicationCreateView
from .views import get_csrf

urlpatterns = [
    path('applications/', ApplicationCreateView.as_view(), name='application-create'),
    path('api/csrf/', get_csrf),
]
