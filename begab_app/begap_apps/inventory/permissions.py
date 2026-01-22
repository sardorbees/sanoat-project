# permissions.py
from rest_framework import permissions

class IsAuthenticatedCustom(permissions.BasePermission):
    """
    Разрешает доступ только авторизованным пользователям.
    Если не авторизован — возвращает сообщение на русском.
    """

    message = "Вы не авторизованы"

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
