from rest_framework import generics
from .models import Branch, Zone, Seat
from .serializers import BranchSerializer, ZoneSerializer, SeatSerializer
from .permissions import IsAuthenticatedCustom

# --------------------------
# Branches
# --------------------------
class BranchListView(generics.ListAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticatedCustom]  # <-- только авторизованные

# --------------------------
# Zones
# --------------------------
class ZoneListView(generics.ListAPIView):
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    permission_classes = [IsAuthenticatedCustom]

# --------------------------
# Seats
# --------------------------
class SeatListView(generics.ListAPIView):
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer
    permission_classes = [IsAuthenticatedCustom]
