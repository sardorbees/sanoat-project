from django.urls import path
from .views import (
    RegisterView,
    VerifyCodeView,
    LoginView,
    ProfileView,
    ResetPasswordSendCodeView,
    ResetPasswordVerifyCodeView,
    SetNewPasswordView,
    VerifyRegisterCodeView,
    VerifyLoginCodeView,
    ResetPasswordSendCodeView,
    ResetPasswordVerifyView,
)

urlpatterns = [
    # Регистрация
    path('register/', RegisterView.as_view(), name='register'),

    # Подтверждение email кодом
    path('verify-code/', VerifyCodeView.as_view(), name='verify-code'),

    # Логин
    path('login/', LoginView.as_view(), name='login'),

    # Профиль (требует токен)
    path('profile/', ProfileView.as_view(), name='profile'),

    # Сброс пароля — отправка кода
    path('reset/send-code/', ResetPasswordSendCodeView.as_view(), name='reset-send-code'),

    # Сброс пароля — проверка кода
    path('reset/verify-code/', ResetPasswordVerifyCodeView.as_view(), name='reset-verify-code'),

    # Сброс пароля — установка нового пароля
    path('reset/new-password/', SetNewPasswordView.as_view(), name='reset-new-password'),

    path("verify-register/", VerifyRegisterCodeView.as_view(), name='verify-register'),

    path("verify-login/", VerifyLoginCodeView.as_view(), name='verify-login'),

    path('send-code/', ResetPasswordSendCodeView.as_view(), name='send-code'),

    path('send-verify/', ResetPasswordVerifyView.as_view(), name='send-verify'),

    # path('register/', RegisterView.as_view(), name='register'),
    # path('login/', LoginView.as_view(), name='login'),
]
