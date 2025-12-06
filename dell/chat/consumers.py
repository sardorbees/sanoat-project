import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from .utils import send_email_async

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # принимаем токен из query string: ws://.../ws/chat/?token=<access>
        token = self.scope['query_string'].decode().split('token=')[-1] if b'token=' in self.scope['query_string'] else None
        self.user = None
        if token:
            try:
                jwt_auth = JWTAuthentication()
                validated = jwt_auth.get_validated_token(token)
                self.user = await database_sync_to_async(jwt_auth.get_user)(validated)
            except Exception:
                self.user = None

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # группы: персональная + общая админ-группа
        self.user_group = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        if self.user.is_staff:
            # админ в группе 'admins' чтобы получать все входящие
            await self.channel_layer.group_add("admins", self.channel_name)

        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        if getattr(self, 'user', None) and self.user.is_staff:
            await self.channel_layer.group_discard("admins", self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Ожидает JSON:
        {
          "action": "send_message",
          "content": "...",
          "message_type": "text",
          "target_user": <id>   # только для admin, у user не указываем
        }
        """
        if text_data is None:
            return

        data = json.loads(text_data)
        action = data.get('action')

        if action == 'send_message':
            content = data.get('content', '')
            message_type = data.get('message_type', 'text')
            # если админ отправляет — target_user обязателен
            if self.user.is_staff:
                target_id = data.get('target_user')
                if not target_id:
                    await self.send_json({"error": "target_user required for admin"})
                    return
                # создаём сообщение для пользователя
                message = await database_sync_to_async(self._create_message_for_user)(target_id, content, message_type)
                # отправляем real-time в группу пользователя и админов
                payload = {
                    "type": "chat.message",
                    "message": ChatMessageSerializer(message).data
                }
                await self.channel_layer.group_send(f"user_{target_id}", payload)
                await self.channel_layer.group_send("admins", payload)  # для отображения в админской сессии
                # email в фоне
                if message.user.email:
                    send_email_async(message.user.email, "Ответ администратора", f"Ответ от админа: '{message.content}'")
                return

            # обычный пользователь отправляет админу — присылаем в группу admins
            message = await database_sync_to_async(self._create_message_from_user)(self.user.id, content, message_type)
            payload = {
                "type": "chat.message",
                "message": ChatMessageSerializer(message).data
            }
            await self.channel_layer.group_send("admins", payload)
            await self.channel_layer.group_send(f"user_{self.user.id}", payload)  # эхо пользователю
            # email пользователю (подтверждение)
            if message.user.email:
                send_email_async(message.user.email, "Вы отправили сообщение администратору", f"Вы отправили сообщение: '{message.content}'")
            return

    def _create_message_for_user(self, user_id, content, message_type):
        # синхронный контекст — вызывается через database_sync_to_async
        try:
            recipient = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError("User not found")
        return ChatMessage.objects.create(user=recipient, is_admin=True, content=content, message_type=message_type)

    def _create_message_from_user(self, user_id, content, message_type):
        u = User.objects.get(id=user_id)
        return ChatMessage.objects.create(user=u, is_admin=False, content=content, message_type=message_type)

    async def chat_message(self, event):
        # отправка JSON клиенту
        await self.send_json({
            "type": "chat.message",
            "message": event["message"]
        })


import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatOnlineConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_group = f"chat_{self.user_id}"

        # Групповое подключение
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        message = data["message"]
        sender = data["sender"]
        is_admin = data["is_admin"]

        # Сохраняем сообщение в базу
        ChatMessage.objects.create(
            user_id=self.user_id,
            content=message,
            is_admin=is_admin,
            message_type="text"
        )

        # Отправляем всем в комнате
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "chat_message",
                "message": message,
                "sender": sender,
                "is_admin": is_admin,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))


import json
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from .models import ChatMessage, OnlineStatus

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        self.user = user
        self.room_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()
        await self.set_online(True)
        await self.notify_online_status()

    async def disconnect(self, close_code):
        await self.set_online(False)
        await self.notify_online_status()
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "send_message":
            await self.handle_message(data)
        elif action == "typing":
            await self.handle_typing(data)
        elif action == "read":
            await self.handle_read(data)

    async def handle_message(self, data):
        recipient_id = data.get("recipient_id")
        content = data.get("content", "")
        image = data.get("image", None)
        file = data.get("file", None)
        voice = data.get("voice", None)

        if not recipient_id:
            return

        message = await self.create_message(recipient_id, content, image, file, voice)

        # Отправка получателю
        await self.channel_layer.group_send(
            f"user_{recipient_id}",
            {
                "type": "chat.message",
                "message": self.message_to_json(message)
            }
        )

        # Отправка себе (чтобы увидеть одну галочку)
        await self.send(text_data=json.dumps({
            "type": "chat.message",
            "message": self.message_to_json(message)
        }))

        # Email уведомление
        recipient = await database_sync_to_async(User.objects.get)(id=recipient_id)
        if recipient.email:
            await database_sync_to_async(send_mail)(
                "Новое сообщение",
                f"Вы получили сообщение: {message.content}",
                "admin@example.com",
                [recipient.email],
                fail_silently=True
            )

    async def handle_typing(self, data):
        is_typing = data.get("typing", False)
        recipient_id = data.get("recipient_id")
        await self.set_typing(is_typing)

        # Уведомляем собеседника
        if recipient_id:
            await self.channel_layer.group_send(
                f"user_{recipient_id}",
                {
                    "type": "typing.status",
                    "user": self.user.username,
                    "typing": is_typing
                }
            )

    async def handle_read(self, data):
        message_id = data.get("message_id")
        if message_id:
            msg = await database_sync_to_async(ChatMessage.objects.get)(id=message_id)
            if msg.recipient == self.user:
                msg.is_read = True
                await database_sync_to_async(msg.save)()
                # Обновляем отправителю (две галочки)
                await self.channel_layer.group_send(
                    f"user_{msg.sender.id}",
                    {
                        "type": "chat.read",
                        "message_id": msg.id
                    }
                )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_status(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_read(self, event):
        await self.send(text_data=json.dumps(event))

    async def notify_online_status(self):
        status = await database_sync_to_async(lambda: OnlineStatus.objects.get_or_create(user=self.user)[0])()
        await self.channel_layer.group_send(
            "online_users",
            {
                "type": "user.status",
                "user": self.user.username,
                "is_online": status.is_online
            }
        )

    @database_sync_to_async
    def set_online(self, status):
        online, _ = OnlineStatus.objects.get_or_create(user=self.user)
        online.is_online = status
        online.last_seen = datetime.now()
        online.save()

    @database_sync_to_async
    def set_typing(self, is_typing):
        online, _ = OnlineStatus.objects.get_or_create(user=self.user)
        online.typing = is_typing
        online.save()

    @database_sync_to_async
    def create_message(self, recipient_id, content, image=None, file=None, voice=None):
        recipient = User.objects.get(id=recipient_id)
        return ChatMessage.objects.create(
            sender=self.user,
            recipient=recipient,
            content=content,
            image=image,
            file=file,
            voice=voice
        )

    def message_to_json(self, message):
        return {
            "id": message.id,
            "sender": message.sender.username,
            "recipient": message.recipient.username,
            "content": message.content,
            "image": message.image.url if message.image else None,
            "file": message.file.url if message.file else None,
            "voice": message.voice.url if message.voice else None,
            "is_read": message.is_read,
            "is_admin": message.sender.is_staff,
            "created_at": str(message.created_at)
        }



import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import OnlineStatus
from datetime import datetime

User = get_user_model()

class OnlineStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
        else:
            self.user = user
            self.group_name = "online_users"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            await self.set_online(user, True)
            await self.notify_status()

    async def disconnect(self, close_code):
        await self.set_online(self.user, False)
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.notify_status()

    async def notify_status(self):
        """Отправляем всем пользователям список online"""
        online_users = await self.get_online_users()
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "online.status",
                "online_users": online_users
            }
        )

    async def online_status(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def set_online(self, user, status):
        online, _ = OnlineStatus.objects.get_or_create(user=user)
        online.is_online = status
        online.last_seen = datetime.now()
        online.save()

    @database_sync_to_async
    def get_online_users(self):
        return list(OnlineStatus.objects.filter(is_online=True).values_list("user__username", flat=True))


import json
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatMessage, OnlineStatus

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        self.user = user
        self.room_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()
        await self.set_online(True)
        await self.notify_online_status()

    async def disconnect(self, close_code):
        await self.set_online(False)
        await self.notify_online_status()
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "send_message":
            await self.handle_message(data)
        elif action == "typing":
            await self.handle_typing(data)
        elif action == "read":
            await self.handle_read(data)

    async def handle_message(self, data):
        recipient_id = data.get("recipient_id")
        if not recipient_id:
            return

        content = data.get("content", "")
        image = data.get("image", None)
        file = data.get("file", None)
        voice = data.get("voice", None)

        message = await self.create_message(recipient_id, content, image, file, voice)

        # Отправка получателю
        await self.channel_layer.group_send(
            f"user_{recipient_id}",
            {
                "type": "chat.message",
                "message": self.message_to_json(message)
            }
        )

        # Отправка себе (1 галочка)
        await self.send(text_data=json.dumps({
            "type": "chat.message",
            "message": self.message_to_json(message)
        }))

    async def handle_typing(self, data):
        recipient_id = data.get("recipient_id")
        is_typing = data.get("typing", False)
        await self.set_typing(is_typing)

        if recipient_id:
            await self.channel_layer.group_send(
                f"user_{recipient_id}",
                {
                    "type": "typing.status",
                    "user": self.user.username,
                    "typing": is_typing
                }
            )

    async def handle_read(self, data):
        message_id = data.get("message_id")
        if message_id:
            msg = await database_sync_to_async(ChatMessage.objects.get)(id=message_id)
            if msg.recipient == self.user:
                msg.is_read = True
                await database_sync_to_async(msg.save)()
                await self.channel_layer.group_send(
                    f"user_{msg.sender.id}",
                    {
                        "type": "chat.read",
                        "message_id": msg.id
                    }
                )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_status(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_read(self, event):
        await self.send(text_data=json.dumps(event))

    async def notify_online_status(self):
        status = await database_sync_to_async(lambda: OnlineStatus.objects.get_or_create(user=self.user)[0])()
        await self.channel_layer.group_send(
            "online_users",
            {
                "type": "user.status",
                "user": self.user.username,
                "is_online": status.is_online
            }
        )

    @database_sync_to_async
    def set_online(self, status):
        online, _ = OnlineStatus.objects.get_or_create(user=self.user)
        online.is_online = status
        online.last_seen = datetime.now()
        online.save()

    @database_sync_to_async
    def set_typing(self, typing):
        online, _ = OnlineStatus.objects.get_or_create(user=self.user)
        online.typing = typing
        online.save()

    @database_sync_to_async
    def create_message(self, recipient_id, content, image=None, file=None, voice=None):
        recipient = User.objects.get(id=recipient_id)
        return ChatMessage.objects.create(
            sender=self.user,
            recipient=recipient,
            content=content,
            image=image,
            file=file,
            voice=voice,
            is_admin=self.user.is_staff
        )

    def message_to_json(self, message):
        return {
            "id": message.id,
            "sender": message.sender.username,
            "recipient": message.recipient.username,
            "content": message.content,
            "image": message.image.url if message.image else None,
            "file": message.file.url if message.file else None,
            "voice": message.voice.url if message.voice else None,
            "is_read": message.is_read,
            "is_admin": message.is_admin,
            "created_at": str(message.created_at)
        }


import json
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatMessage, OnlineStatus

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        self.user = user
        self.room_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()
        await self.set_online(True)
        await self.notify_online_status()

    async def disconnect(self, close_code):
        await self.set_online(False)
        await self.notify_online_status()
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "send_message":
            await self.handle_message(data)
        elif action == "message_read":
            await self.handle_read(data)

    async def handle_message(self, data):
        recipient_id = data.get("recipient_id")
        content = data.get("content", "")
        if not recipient_id or not content:
            return

        recipient = await database_sync_to_async(User.objects.get)(id=recipient_id)
        msg = await database_sync_to_async(ChatMessage.objects.create)(
            sender=self.user,
            recipient=recipient,
            content=content
        )

        # Отправка получателю (для 1 галочки)
        await self.channel_layer.group_send(
            f"user_{recipient.id}",
            {
                "type": "chat.message",
                "message": self.message_to_json(msg)
            }
        )

        # Отправка себе (отображение отправленного сообщения)
        await self.send(text_data=json.dumps({
            "type": "chat.message",
            "message": self.message_to_json(msg)
        }))

    async def handle_read(self, data):
        message_id = data.get("message_id")
        if not message_id:
            return

        msg = await database_sync_to_async(ChatMessage.objects.get)(id=message_id)
        if msg.recipient == self.user and not msg.is_read:
            msg.is_read = True
            await database_sync_to_async(msg.save)()

            # Уведомление отправителю о прочтении (2 галочки)
            await self.channel_layer.group_send(
                f"user_{msg.sender.id}",
                {
                    "type": "chat.read",
                    "message_id": msg.id
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat.message",
            "message": event["message"]
        }))

    async def chat_read(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat.read",
            "message_id": event["message_id"]
        }))

    async def notify_online_status(self):
        status = await database_sync_to_async(lambda: OnlineStatus.objects.get_or_create(user=self.user)[0])()
        await self.channel_layer.group_send(
            "online_users",
            {
                "type": "user.status",
                "user": self.user.username,
                "is_online": status.is_online
            }
        )

    @database_sync_to_async
    def set_online(self, status):
        obj, _ = OnlineStatus.objects.get_or_create(user=self.user)
        obj.is_online = status
        obj.last_seen = datetime.now()
        obj.save()

    def message_to_json(self, message):
        return {
            "id": message.id,
            "sender": message.sender.username,
            "recipient": message.recipient.username,
            "content": message.content,
            "is_read": message.is_read,
            "created_at": str(message.created_at)
        }


import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatMessage, OnlineStatus
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        self.user = user
        self.room_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()
        await self.set_online(True)

    async def disconnect(self, close_code):
        await self.set_online(False)
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "send_message":
            await self.send_message(data)
        elif action == "typing":
            await self.set_typing(data.get("typing", False))

    async def send_message(self, data):
        recipient_id = data.get("recipient_id")
        content = data.get("content", "")
        if not recipient_id or not content:
            return

        recipient = await database_sync_to_async(User.objects.get)(id=recipient_id)
        msg = await database_sync_to_async(ChatMessage.objects.create)(
            sender=self.user,
            recipient=recipient,
            content=content,
            is_admin=self.user.is_staff
        )

        payload = {
            "id": msg.id,
            "sender": self.user.username,
            "recipient": recipient.username,
            "content": content,
            "is_read": msg.is_read,
            "created_at": str(msg.created_at),
        }

        # Отправляем получателю
        await self.channel_layer.group_send(
            f"user_{recipient.id}",
            {"type": "chat.message", "message": payload}
        )

        # Отправляем себе
        await self.send(text_data=json.dumps({"message": payload}))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def set_online(self, online):
        obj, _ = OnlineStatus.objects.get_or_create(user=self.user)
        obj.is_online = online
        obj.last_seen = datetime.now()
        obj.save()

    @database_sync_to_async
    def set_typing(self, typing):
        obj, _ = OnlineStatus.objects.get_or_create(user=self.user)
        obj.typing = typing
        obj.save()

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from chat.models import OnlineStatus
from django.contrib.auth.models import User

class OnlineStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            self.user = self.scope["user"]

            obj, created = OnlineStatus.objects.get_or_create(user=self.user)
            obj.last_seen = timezone.now()
            obj.save()

            await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        obj, created = OnlineStatus.objects.get_or_create(user=self.user)
        obj.last_seen = timezone.now()
        obj.save()

    async def disconnect(self, close_code):
        obj, created = OnlineStatus.objects.get_or_create(user=self.user)
        obj.last_seen = timezone.now()
        obj.save()


import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from django.utils import timezone
from .models import OnlineStatus


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_group_name = f"chat_{self.user_id}"

        # Присоединяемся в WebSocket комнату
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Обновляем статус Online
        user = User.objects.get(id=self.user_id)
        status, _ = OnlineStatus.objects.get_or_create(user=user)
        status.last_seen = timezone.now()
        status.save()

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "status", "online": True, "typing": False}
        )

    async def disconnect(self, close_code):
        # Ставим OFFLINE + записываем last_seen
        user = User.objects.get(id=self.user_id)
        status = user.online_status
        status.last_seen = timezone.now()
        status.is_typing = False
        status.save()

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "status", "online": False, "typing": False}
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Если пишет — индикация typing...
        if data.get("typing") is not None:
            user = User.objects.get(id=self.user_id)
            status = user.online_status
            status.is_typing = data["typing"]
            status.last_seen = timezone.now()
            status.save()

            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "status", "online": True, "typing": data["typing"]}
            )

    async def status(self, event):
        await self.send(text_data=json.dumps({
            "online": event["online"],
            "typing": event["typing"],
        }))


# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.me = self.scope["user"]
        self.other_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room = f"chat_{min(self.me.id, self.other_id)}_{max(self.me.id, self.other_id)}"

        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)

        # ========== TEXT MESSAGE ==========
        if data["type"] == "message":
            msg = Message.objects.create(
                sender=self.me,
                receiver_id=self.other_id,
                text=data["text"],
            )

            await self.channel_layer.group_send(self.room, {
                "type": "chat_message",
                "message_id": msg.id,
                "text": msg.text,
                "sender": self.me.id,
                "receiver": self.other_id,
                "delivered": True,
                "seen": False,
            })

        # ========== DELIVERED STATUS ==========
        if data["type"] == "delivered":
            msg = Message.objects.get(id=data["message_id"])
            msg.delivered = True
            msg.save()

        # ========== SEEN STATUS ==========
        if data["type"] == "seen":
            msg = Message.objects.get(id=data["message_id"])
            msg.seen = True
            msg.save()

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Message, OnlineStatus
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.me = self.scope["user"]
        self.other_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room = f"chat_{min(self.me.id, self.other_id)}_{max(self.me.id, self.other_id)}"

        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()

        # Online
        await self.set_online(True)

    async def disconnect(self, close_code):
        await self.set_online(False)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data["type"] == "message":
            msg = Message.objects.create(
                sender=self.me,
                receiver_id=self.other_id,
                text=data.get("text", ""),
                image=data.get("image", None),
                audio=data.get("audio", None),
                file=data.get("file", None)
            )
            await self.send_chat(msg)

        if data["type"] == "typing":
            await self.set_typing(data["is_typing"])

        if data["type"] == "seen":
            msg = Message.objects.get(id=data["message_id"])
            msg.seen = True
            msg.save()
            await self.send_chat(msg)

    async def send_chat(self, msg):
        event = {
            "id": msg.id,
            "sender": msg.sender.username,
            "receiver": msg.receiver.username,
            "text": msg.text,
            "image": msg.image.url if msg.image else None,
            "audio": msg.audio.url if msg.audio else None,
            "file": msg.file.url if msg.file else None,
            "delivered": True,
            "seen": msg.seen,
            "timestamp": str(msg.timestamp)
        }
        await self.channel_layer.group_send(self.room, {
            "type": "chat.message",
            "message": event
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def set_online(self, status):
        obj, _ = OnlineStatus.objects.get_or_create(user=self.me)
        obj.is_online = status
        obj.last_seen = timezone.now()
        obj.save()

    @database_sync_to_async
    def set_typing(self, status):
        obj, _ = OnlineStatus.objects.get_or_create(user=self.me)
        obj.is_typing = status
        obj.save()