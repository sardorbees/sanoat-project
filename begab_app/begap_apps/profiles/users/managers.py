# users/managers.py
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, phone, nickname, password=None):
        if not phone:
            raise ValueError('Phone is required')

        user = self.model(phone=phone, nickname=nickname)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, nickname, password):
        user = self.create_user(phone, nickname, password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user
