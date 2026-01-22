from django.urls import path
from .views import BannerListView, ClubListView

urlpatterns = [
    path("banners/", BannerListView.as_view(), name="banner_list"),
    path("clubs/", ClubListView.as_view(), name="club_list"),
]
