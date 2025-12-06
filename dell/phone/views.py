import random
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import PhoneOTP
from .serializers import SendOTPSerializer, VerifyOTPSerializer
from .utils import send_sms
from rest_framework_simplejwt.tokens import RefreshToken

def generate_code():
    return str(random.randint(100000, 999999))

@api_view(["POST"])
def send_otp(request):
    serializer = SendOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone = serializer.validated_data["phone"]

    last_otp = PhoneOTP.objects.filter(phone=phone).order_by('-created_at').first()
    if last_otp and not last_otp.can_resend():
        return Response({"error": "Повторная отправка через 60 секунд"}, status=400)

    code = generate_code()
    PhoneOTP.objects.create(phone=phone, code=code)

    sms_res = send_sms(phone, f"Ваш код подтверждения: {code}")
    return Response({"message": "OTP отправлен", "sms_response": sms_res})

@api_view(["POST"])
def verify_otp(request):
    serializer = VerifyOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone = serializer.validated_data["phone"]
    code = serializer.validated_data["code"]

    try:
        otp = PhoneOTP.objects.get(phone=phone, code=code)
    except PhoneOTP.DoesNotExist:
        return Response({"error": "Неверный код"}, status=400)

    if otp.is_expired():
        return Response({"error": "Код истёк"}, status=400)

    otp.is_verified = True
    otp.save()

    # JWT для идентификатора пользователя (если нет модели User, можно использовать phone)
    refresh = RefreshToken.for_user(1)  # временный user_id=1
    return Response({
        "message": "Код подтверждён",
        "refresh": str(refresh),
        "access": str(refresh.access_token)
    })
