from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from .models import BlockedIP, AttackLog
from .serializers import BlockIPSerializer, CheckIPSerializer, AttackLogSerializer

class SecurityStatusView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        blocked_count = BlockedIP.objects.count()
        attacks = AttackLog.objects.count()
        return Response({
            "blocked_ips": blocked_count,
            "attack_logs": attacks
        })

class BlockIPView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = BlockIPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip = serializer.validated_data["ip"]
        reason = serializer.validated_data.get("reason", "")
        minutes = serializer.validated_data.get("minutes", 60)
        expires_at = timezone.now() + timezone.timedelta(minutes=minutes)
        obj, created = BlockedIP.objects.update_or_create(ip=ip, defaults={"reason": reason, "expires_at": expires_at})
        return Response({"blocked": True, "ip": obj.ip, "expires_at": obj.expires_at})

class CheckIPStatusView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = CheckIPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip = serializer.validated_data["ip"]
        obj = BlockedIP.objects.filter(ip=ip).first()
        return Response({"ip": ip, "blocked": bool(obj and obj.is_active()), "reason": obj.reason if obj else ""})

class AttackLogListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        logs = AttackLog.objects.all()[:200]
        serializer = AttackLogSerializer(logs, many=True)
        return Response(serializer.data)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserSession
from .serializers import UserSessionSerializer

class UserSessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = UserSession.objects.filter(user=request.user).order_by('-created_at')
        serializer = UserSessionSerializer(sessions, many=True)
        return Response(serializer.data)
