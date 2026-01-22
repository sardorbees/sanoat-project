from django.urls import path
from .views import PaymentMethodListView

urlpatterns = [
    path('methods/', PaymentMethodListView.as_view()),
]
