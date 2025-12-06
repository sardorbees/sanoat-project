from rest_framework import generics, permissions, serializers
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import ChatMessage, BlockedUser
from .serializers import ChatMessageSerializer
from .utils import send_email_async, contains_bad_words

User = get_user_model()


class ChatMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [permissions.IsAuthenticated]

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ChatMessage.objects.all().order_by("created_at")
        return ChatMessage.objects.filter(user=user).order_by("created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_admin=self.request.user.is_staff)
        user = self.request.user
        ip = self.get_client_ip()

        # Проверка блокировки по пользователю и IP
        if BlockedUser.objects.filter(user=user).exists() or BlockedUser.objects.filter(ip_address=ip).exists():
            raise serializers.ValidationError("Вы заблокированы и не можете отправлять сообщения.")

        # Проверка на запрещённые слова
        content = serializer.validated_data.get('content', '')
        if contains_bad_words(content):
            BlockedUser.objects.create(user=user, ip_address=ip)
            raise serializers.ValidationError("Вы использовали запрещённые слова. Ваш аккаунт заблокирован.")

        # USER → ADMIN
        if not user.is_staff:
            instance = serializer.save(user=user, is_admin=False)
            if user.email:
                send_email_async(
                    user.email,
                    "Вы отправили сообщение админу",
                    f"Ваше сообщение: '{instance.content}'"
                )
            return instance

        # ADMIN → USER
        recipient_id = self.request.data.get("user")
        if not recipient_id:
            raise serializers.ValidationError("Укажите ID пользователя для ответа.")

        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден.")

        instance = serializer.save(user=recipient, is_admin=True)
        if recipient.email:
            send_email_async(
                recipient.email,
                "Ответ администратора",
                f"Админ ответил: '{instance.content}'"
            )
        return instance

# MARK AS READ (PATCH)
@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def mark_read(request, pk):
    """
    Помечает сообщение как прочитанное.
    Доступно только для владельца сообщения.
    """
    try:
        message = ChatMessage.objects.get(pk=pk)
    except ChatMessage.DoesNotExist:
        return Response({"detail": "Сообщение не найдено."}, status=404)

    if request.user != message.user:
        return Response({"detail": "Нет доступа."}, status=403)

    message.is_read = True
    message.save()
    return Response({"status": "read"})


from rest_framework import generics, permissions, serializers
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth import get_user_model
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from .utils import send_email_async  # функция для отправки email

User = get_user_model()

class ChatView(generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        chat_user_id = self.request.query_params.get("user")

        if user.is_staff and chat_user_id:
            return ChatMessage.objects.filter(user_id=chat_user_id).order_by("created_at")
        return ChatMessage.objects.filter(user=user).order_by("created_at")

    def perform_create(self, serializer):
        user = self.request.user

        if not user.is_staff:
            instance = serializer.save(user=user, is_admin=False)
            if user.email:
                send_email_async(
                    user.email,
                    "Вы отправили сообщение админу",
                    f"Ваше сообщение: {instance.content}"
                )
            return instance

        recipient_id = self.request.data.get("user")
        if not recipient_id:
            raise serializers.ValidationError("Укажите ID пользователя для ответа.")

        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден.")

        instance = serializer.save(user=recipient, is_admin=True)
        if recipient.email:
            send_email_async(
                recipient.email,
                "Ответ администратора",
                f"Админ ответил: {instance.content}"
            )
        return instance


from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import BlockedUser

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        ip = self.context['request'].META.get('REMOTE_ADDR')
        if BlockedUser.objects.filter(ip_address=ip).exists():
            raise serializers.ValidationError("С этого IP регистрация запрещена.")

        user = User.objects.create_user(**validated_data)
        return user

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def chat_page(request):
    return render(request, 'chat/chat.html')  # путь к вашему шаблону


from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import OnlineStatus

@login_required
def ping(request):
    status, created = OnlineStatus.objects.get_or_create(user=request.user)
    status.last_seen = timezone.now()
    status.save()
    return JsonResponse({"status": "updated"})


from django.shortcuts import render
from chat.models import OnlineStatus
from django.contrib.auth.models import User

def chat_view(request, username):
    user = User.objects.get(username=username)
    online = OnlineStatus.objects.get_or_create(user=user)[0]

    return render(request, "chat.html", {
        "chat_user": user,
        "online": online,
    })


from django.http import JsonResponse
from django.contrib.auth.models import User


def get_online_status(request, user_id):
    user = User.objects.get(id=user_id)
    status = user.online_status.is_online
    last_seen = user.online_status.last_seen.strftime("%H:%M:%S")
    return JsonResponse({"online": status, "last_seen": last_seen})


from django.shortcuts import render
from django.contrib.auth.models import User
from .models import OnlineStatus, ChatMessage

def chat_home(request):
    users = User.objects.exclude(id=request.user.id)
    statuses = {u.id: OnlineStatus.objects.filter(user=u).first() for u in users}
    return render(request, 'chat/home.html', {'users': users, 'statuses': statuses})

def chat_page(request, user_id):
    other_user = User.objects.get(id=user_id)
    messages = ChatMessage.objects.filter(
        sender_id__in=[request.user.id, user_id],
        receiver_id__in=[request.user.id, user_id]
    ).order_by('timestamp')
    return render(request, 'chat/chat.html', {'other_user': other_user, 'messages': messages})
