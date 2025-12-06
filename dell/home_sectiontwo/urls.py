from django.urls import path
from .views import InfoListCreateView, InfoRetrieveUpdateView

urlpatterns = [
    path('info/', InfoListCreateView.as_view(), name='info-list'),
    path('info/<int:pk>/', InfoRetrieveUpdateView.as_view(), name='info-detail'),
]
