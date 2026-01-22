# bookings/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, BookingHistoryView, BookingCancelView, BranchAvailabilityView, init_booking, payment_webhook

# -----------------------------
# ViewSet для CRUD бронирований
# -----------------------------
router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')

# -----------------------------
# Паттерны для истории и отмены
# -----------------------------
urlpatterns = [
    path('history/', BookingHistoryView.as_view(), name='booking-history'),
    path('<uuid:id>/cancel/', BookingCancelView.as_view(), name='booking-cancel'),
    path('', include(router.urls)),
    path('branches/<int:id>/availability', BranchAvailabilityView.as_view()),
    path('bookings/init', init_booking),
    path('bookings/webhook', payment_webhook),
]
