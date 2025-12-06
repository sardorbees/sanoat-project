from django.urls import path
from .views import IconTitleListCreateView, IconTitleDetailView

urlpatterns = [
    path('icon-title/', IconTitleListCreateView.as_view()),
    path('icon-title/<int:pk>/', IconTitleDetailView.as_view()),
]
