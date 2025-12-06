from rest_framework import viewsets, permissions
from .models import IndustryArticle
from .serializers import IndustryArticleSerializer

class IndustryArticleViewSet(viewsets.ModelViewSet):
    queryset = IndustryArticle.objects.all()
    serializer_class = IndustryArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "id"
