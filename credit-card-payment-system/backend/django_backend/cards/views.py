from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Card
from .serializers import CardSerializer

class CardListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CardSerializer

    def get_queryset(self):
        return Card.objects.filter(user=self.request.user).order_by("-created_at")

class CardDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CardSerializer

    def get_queryset(self):
        return Card.objects.filter(user=self.request.user)
