# bookings/views.py
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets

from .models import Booking
from .serializers import BookingSerializer, BookingHistorySerializer


# -------------------------
# История бронирований
# -------------------------
class BookingHistoryView(ListAPIView):
    serializer_class = BookingHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # сортировка по start_time (раньше была visit_datetime)
        return Booking.objects.filter(user=self.request.user).order_by('-start_time')


# -------------------------
# Отмена бронирования
# -------------------------
class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        # выбираем только брони, которые ещё не завершены
        booking = get_object_or_404(
            Booking,
            id=id,
            user=request.user,
            status__in=[Booking.Status.PENDING, Booking.Status.PAID, Booking.Status.SYNCED]
        )

        # нельзя отменять прошедшее бронирование
        if booking.start_time < timezone.now():
            return Response(
                {'detail': 'Нельзя отменить прошедшее бронирование'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # считаем штраф, если отмена поздняя
        if not booking.can_cancel():
            penalty = booking.calculate_penalty()
            booking.penalty_amount = penalty
        else:
            penalty = 0

        # обновляем статус
        booking.status = Booking.Status.CANCELLED
        booking.save()

        return Response({
            'status': 'cancelled',
            'penalty': penalty
        })


# -------------------------
# CRUD бронирований через ViewSet
# -------------------------
class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # чтобы юзер видел только свои брони
        return Booking.objects.filter(user=self.request.user)


from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import Branch, Seat, Booking
import redis
import datetime

# Настройка Redis
r = redis.Redis(host='localhost', port=6379, db=0)


class BranchAvailabilityView(APIView):
    def get(self, request, id):
        date_str = request.GET.get("date")
        time_str = request.GET.get("time")
        if not date_str or not time_str:
            return Response({"error": "date and time required"}, status=400)

        requested_time = datetime.datetime.fromisoformat(f"{date_str}T{time_str}")
        branch = Branch.objects.get(pk=id)
        seats = branch.seats.all()
        bookings = Booking.objects.filter(
            seat__branch=branch,
            start_time__lte=requested_time,
            end_time__gt=requested_time,
        )

        availability = []
        for seat in seats:
            status = seat.status  # DEFAULT: FREE / MAINTENANCE
            # Проверка активных бронирований
            if bookings.filter(seat=seat).exists():
                status = "BUSY_BY_BOOKING"
            # Проверка live из Redis (только если сейчас)
            if requested_time.date() == timezone.now().date() and requested_time.hour == timezone.now().hour:
                live_status = r.get(f"seat:{seat.id}:status")
                if live_status:
                    status = live_status.decode()
            availability.append({
                "seat_id": seat.id,
                "number": seat.number,
                "status": status
            })
        return Response(availability)

from rest_framework import status
from rest_framework.decorators import api_view
from django.utils import timezone
from .models import Booking, Seat
import redis, uuid

r = redis.Redis(host='localhost', port=6379, db=0)

@api_view(['POST'])
def init_booking(request):
    user = request.user
    seat_id = request.data.get("seat_id")
    start_time = request.data.get("start_time")
    end_time = request.data.get("end_time")

    if not all([seat_id, start_time, end_time]):
        return Response({"error": "seat_id, start_time, end_time required"}, status=400)

    lock_key = f"lock:seat:{seat_id}:{start_time}:{end_time}"
    # Пытаемся установить lock в Redis (expire 60 сек)
    if not r.set(lock_key, "locked", nx=True, ex=60):
        return Response({"error": "Seat is currently locked"}, status=409)

    seat = Seat.objects.get(pk=seat_id)
    booking = Booking.objects.create(
        user=user,
        seat=seat,
        start_time=start_time,
        end_time=end_time,
        status="PENDING"
    )

    # Тут можно вызвать платежку и вернуть ссылку
    payment_link = f"https://pay.example.com/{booking.id}"
    return Response({"booking_id": booking.id, "payment_link": payment_link})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Booking
import json

@csrf_exempt
def payment_webhook(request):
    data = json.loads(request.body)
    booking_id = data.get("booking_id")
    payment_status = data.get("status")

    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({"error": "Booking not found"}, status=404)

    if payment_status == "PAID":
        booking.status = "PAID"
        booking.save()
        # Синхронизация с iCafe
        # r.set(f"seat:{booking.seat.id}:status", "BUSY_LIVE")  # если нужно
        # Здесь вызов iCafe API
        booking.status = "SYNCED"
        booking.save()

    return JsonResponse({"status": "ok"})
