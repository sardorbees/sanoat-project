from django.urls import path
from .views import (
    BlockIPView,
    CheckIPStatusView,
    SecurityStatusView,
    AttackLogListView,
    UserSessionsView
)

urlpatterns = [
    # Проверка текущего статуса безопасности
    path('status/', SecurityStatusView.as_view(), name='security-status'),

    # Проверка заблокирован ли IP
    path('ip-status/', CheckIPStatusView.as_view(), name='check-ip-status'),

    # Вручную заблокировать IP (например админ панель)
    path('block-ip/', BlockIPView.as_view(), name='block-ip'),

    # Логи попыток атак
    path('attack-logs/', AttackLogListView.as_view(), name='attack-logs'),

    # какой устройства зашел можно посмотреть
    path('my-sessions/', UserSessionsView.as_view(), name='my-sessions'),
]
