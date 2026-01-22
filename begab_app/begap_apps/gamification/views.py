from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated

from .models import UserProfile
from .serializers import UserProfileSerializer


class MyGamificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_anonymous:
            raise NotAuthenticated("Authentication required")

        profile, _ = UserProfile.objects.get_or_create(
            user=request.user
        )
        return Response(UserProfileSerializer(profile).data)
