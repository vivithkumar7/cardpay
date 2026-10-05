from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    card_mask = serializers.CharField(source="card.masked_card_number", read_only=True)

    class Meta:
        model = Transaction
        fields = (
            "id", "amount", "currency", "status", "reference",
            "failure_reason", "card_mask", "created_at", "updated_at"
        )
