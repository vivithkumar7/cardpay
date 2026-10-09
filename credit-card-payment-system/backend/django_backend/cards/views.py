from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.role_permissions import CanManagePersonalCards
from .models import Card
from .serializers import CardSerializer
from accounts.notifications import queue_account_email
from transactions.models import Transaction

class CardListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, CanManagePersonalCards]
    serializer_class = CardSerializer

    def get_queryset(self):
        return Card.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        card = serializer.save()
        queue_account_email(
            card.user,
            "New payment card added",
            f"A card ending in {card.last4} was added to your PaySecure account.",
        )

class CardDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CanManagePersonalCards]
    serializer_class = CardSerializer

    def get_queryset(self):
        return Card.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        card = self.get_object()
        if Transaction.objects.filter(card=card).exists():
            return Response(
                {"detail": "A card with transaction history cannot be removed."},
                status=status.HTTP_409_CONFLICT,
            )
        queue_account_email(
            card.user,
            "Payment card removed",
            f"The card ending in {card.last4} was removed from your PaySecure account.",
        )
        card.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
