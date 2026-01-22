# app/urls.py
from django.urls import path
from .views import MyGamificationView

urlpatterns = [
    path("me/gamification/", MyGamificationView.as_view()),
]