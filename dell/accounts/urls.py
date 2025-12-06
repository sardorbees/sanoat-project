from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, UserProfileView, LogoutView, DashboardView, ChangePasswordView, AddressListCreateView, AddressDetailView
from .serializers import CustomTokenSerializer
from .views import ResetPasswordAPIView
from .views import ResetPasswordAPIView, VerifyCodeView

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("reset-password/", ResetPasswordAPIView.as_view()),
    path("login/", CustomLoginView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("profile/", UserProfileView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("edit-profile/", UserProfileView.as_view(), name="edit-profile"),
    path("dashboard/", DashboardView.as_view()),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path('addresses/', AddressListCreateView.as_view(), name='address-list-create'),
    path('addresses/<int:address_id>/', AddressDetailView.as_view(), name='address-detail'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify-code'),
]
