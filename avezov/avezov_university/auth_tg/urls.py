from django.urls import path
from .views import (
    RegisterAPIView, LoginAPIView, VerifyCodeAPIView,
    ResetPasswordAPIView, VerifyResetCodeAPIView, NewPasswordAPIView,
    ProfileAPIView, ResendCodeAPIView, GoogleAuthAPIView, ProfileView, RegisterVerifyCodeAPIView, LoginVerifyCodeAPIView,
    ForgotPasswordAPIView,
    ResetPasswordAPIView,
    ChangesPasswordAPIView,
    ForgotssPasswordAPIView,
    ResetdPasswordAPIView,
    RequestPasswordResetView, VerifyPasswordResetView,
    ResetPasswordRequestView, ResetPasswordConfirmView, ChangePasswordView, SendOTPAPIView, ConfirmChangePasswordView, ConfirmLoginAPIView, ConfirmedChangePasswordView
)
from . import views

urlpatterns = [
    path('forgot-end-password/', ForgotssPasswordAPIView.as_view(), name='forgot-end-password'),
    path('reset-password/', ResetdPasswordAPIView.as_view(), name='reset-password'),

    # path("register/", RegisterAPIView.as_view(), name="register"),
    # path("login/", LoginAPIView.as_view(), name="login"),
    # path('verify-code/', VerifyCodeAPIView.as_view(), name='verify-code'),
    # path("reset-password/", ResetPasswordAPIView.as_view(), name="reset_password"),
    # path("verify-reset-code/", VerifyResetCodeAPIView.as_view(), name="verify_reset_code"),
    # path("new-password/", NewPasswordAPIView.as_view(), name="new_password"),
    # path('telegram-auth/', views.telegram_auth, name='telegram_auth'),
    # path("profile/<int:user_id>/", ProfileAPIView.as_view(), name="profile"),
    # path('create_code/', CreateTelegramCode.as_view(), name='create_code'),
    # path("forgot-password/", ForgotPasswordAPIView.as_view(), name="forgot-password"),

    path('resend-code/', ResendCodeAPIView.as_view(), name='resend-code'),
    path('google/', GoogleAuthAPIView.as_view(), name='google-auth'),
    path('profile/', ProfileView.as_view(), name='profile'),

    path('registers/', RegisterAPIView.as_view(), name='register'),
    path('registers-verify-code/', RegisterVerifyCodeAPIView.as_view(), name='register-verify-code'),
    path("logins/", LoginAPIView.as_view(), name="login"),
    path('login-verify-code/', LoginVerifyCodeAPIView.as_view(), name='login-verify-code'),

    path('forgot-password/', ForgotPasswordAPIView.as_view(), name='forgots-password'),
    path('resets-password/', ResetPasswordAPIView.as_view(), name='resets-password'),
    path('changes-password/', ChangesPasswordAPIView.as_view(), name='changes-password'),

    path('auth/forgot-password/', ResetPasswordRequestView.as_view(), name='forgot-password'),
    path('auth/reset-password/<uid>/<token>/', ResetPasswordConfirmView.as_view(), name='reset-password'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),

    path('send-otp/', SendOTPAPIView.as_view(), name='send-otp'),
    path('confirm-login/', ConfirmLoginAPIView.as_view(), name='confirm-login'),
    path('confirmed-change-password/', ConfirmChangePasswordView.as_view(), name='confirmed-change-password'),

    path("password-reset/request/", RequestPasswordResetView.as_view(), name="password_reset_request"),
    path("password-reset/verify/", VerifyPasswordResetView.as_view(), name="password_reset_verify"),
]
