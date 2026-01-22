# users/urls.py
from django.urls import path
from .views import GetMeView, UpdateProfileView, LogoutProfileView

urlpatterns = [
    path("me/", GetMeView.as_view(), name="get_me"),
    path("me/update/", UpdateProfileView.as_view(), name="update_profile"),
    path("me/logout/", LogoutProfileView.as_view(), name="logout_profile"),
]
