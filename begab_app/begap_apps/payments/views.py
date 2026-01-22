from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from .models import PaymentMethod
from .serializers import PaymentMethodSerializer

class PaymentMethodListView(ListAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)
