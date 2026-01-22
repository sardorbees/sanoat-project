from django.urls import path
from .views import BranchListView, ZoneListView, SeatListView

urlpatterns = [
    path("branches/", BranchListView.as_view(), name="branch_list"),
    path("zones/", ZoneListView.as_view(), name="zone_list"),
    path("seats/", SeatListView.as_view(), name="seat_list"),
]
