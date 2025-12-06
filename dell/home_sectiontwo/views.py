from rest_framework import generics
from .models import Info
from .serializers import InfoSerializer

class InfoListCreateView(generics.ListCreateAPIView):
    queryset = Info.objects.all()
    serializer_class = InfoSerializer

class InfoRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Info.objects.all()
    serializer_class = InfoSerializer
