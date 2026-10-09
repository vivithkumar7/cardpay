from decimal import Decimal

from rest_framework import serializers

from accounts.models import UserCreditProfile
from transactions.models import Transaction
from .models import Card


class AdminCardSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    account_credit_limit = serializers.SerializerMethodField()
    credit_limit = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Card
        fields = (
            "id",
            "username",
            "email",
            "card_type",
            "masked_card_number",
            "last4",
            "card_holder_name",
            "expiry_month",
            "expiry_year",
            "is_active",
            "account_credit_limit",
            "credit_limit",
            "created_at",
        )
        read_only_fields = (
            "id",
            "username",
            "email",
            "card_type",
            "masked_card_number",
            "last4",
            "card_holder_name",
            "expiry_month",
            "expiry_year",
            "account_credit_limit",
            "created_at",
        )

    def get_account_credit_limit(self, card):
        profile = getattr(card.user, "credit_profile", None)
        return profile.credit_limit if profile else Decimal("0.00")

    def update(self, instance, validated_data):
        credit_limit = validated_data.pop("credit_limit", None)
        instance = super().update(instance, validated_data)
        if credit_limit is not None:
            profile, _ = UserCreditProfile.objects.get_or_create(user=instance.user)
            profile.credit_limit = credit_limit
            profile.save(update_fields=["credit_limit"])
        return instance


class AdminCardActivitySerializer(serializers.ModelSerializer):
    card_mask = serializers.CharField(source="card.masked_card_number", read_only=True)
    card_holder_name = serializers.CharField(
        source="card.card_holder_name", read_only=True
    )

    class Meta:
        model = Transaction
        fields = (
            "id",
            "amount",
            "currency",
            "category",
            "status",
            "reference",
            "failure_reason",
            "fraud_status",
            "card_mask",
            "card_holder_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
