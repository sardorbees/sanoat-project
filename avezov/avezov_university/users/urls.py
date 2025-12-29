from django.urls import path
from .views import (
    RegisterView, RegisterVerifyCodeView,
    LoginView, LoginVerifyCodeView,
    ProfileView
)

app_name = 'auth'

urlpatterns = [
    # Register
    path('auth_tg/register/', RegisterView.as_view(), name='register'),
    path('auth_tg/register-verify-code/', RegisterVerifyCodeView.as_view(), name='register_verify'),

    # Login
    path('auth_tg/login/', LoginView.as_view(), name='login'),
    path('auth_tg/login-verify-code/', LoginVerifyCodeView.as_view(), name='login_verify'),

    # Profile
    path('auth_tg/profile/', ProfileView.as_view(), name='profile'),
]
