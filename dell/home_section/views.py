from rest_framework import generics
from .models import IconTitle
from .serializers import IconTitleSerializer

class IconTitleListCreateView(generics.ListCreateAPIView):
    queryset = IconTitle.objects.all()
    serializer_class = IconTitleSerializer

class IconTitleDetailView(generics.RetrieveUpdateAPIView):
    queryset = IconTitle.objects.all()
    serializer_class = IconTitleSerializer
