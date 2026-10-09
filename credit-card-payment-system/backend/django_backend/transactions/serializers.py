from rest_framework import serializers
from .models import FraudAlert, Transaction

class TransactionSerializer(serializers.ModelSerializer):
    card_mask = serializers.CharField(source="card.masked_card_number", read_only=True)

    class Meta:
        model = Transaction
        fields = (
            "id", "amount", "currency", "category", "status", "reference",
            "failure_reason", "fraud_status", "card_mask", "created_at", "updated_at"
        )


class FraudAlertSerializer(serializers.ModelSerializer):
    reference = serializers.CharField(source="transaction.reference", read_only=True)
    amount = serializers.DecimalField(
        source="transaction.amount",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    card_last4 = serializers.CharField(
        source="transaction.card.last4",
        read_only=True,
    )
    username = serializers.SerializerMethodField()

    class Meta:
        model = FraudAlert
        fields = (
            "id",
            "reference",
            "username",
            "amount",
            "card_last4",
            "rule_codes",
            "review_status",
            "reviewed_by",
            "reviewed_at",
            "detected_at",
        )
        read_only_fields = fields

    def get_username(self, alert):
        return alert.user.get_username() if alert.user else ""


class FraudAlertReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = FraudAlert
        fields = ("review_status",)

    def validate_review_status(self, value):
        if value not in {
            FraudAlert.ReviewStatus.REVIEWED,
            FraudAlert.ReviewStatus.FALSE_POSITIVE,
        }:
            raise serializers.ValidationError(
                "Review status must be REVIEWED or FALSE_POSITIVE."
            )
        return value
