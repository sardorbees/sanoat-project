from rest_framework import generics, permissions
from .models import Banner, Club
from .serializers import BannerSerializer, ClubSerializer

# Список баннеров на главной
class BannerListView(generics.ListAPIView):
    queryset = Banner.objects.filter(is_active=True)
    serializer_class = BannerSerializer
    permission_classes = [permissions.AllowAny]  # Доступно без авторизации


# Список клубов
class ClubListView(generics.ListAPIView):
    queryset = Club.objects.all()
    serializer_class = ClubSerializer
    permission_classes = [permissions.AllowAny]
