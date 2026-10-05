import re
from datetime import date
from rest_framework import serializers
from .models import Card

class CardSerializer(serializers.ModelSerializer):
    # write-only fields are accepted to create a masked representation,
    # then immediately discarded. They are NEVER stored.
    card_number = serializers.CharField(write_only=True, min_length=13, max_length=19)
    cvv = serializers.CharField(write_only=True, min_length=3, max_length=4)

    class Meta:
        model = Card
        fields = (
            "id", "card_type", "card_holder_name", "expiry_month",
            "expiry_year", "card_number", "cvv", "masked_card_number",
            "last4", "created_at"
        )
        read_only_fields = ("id", "masked_card_number", "last4", "created_at")

    def validate_card_number(self, value):
        value = re.sub(r"[\s-]", "", value)
        if not value.isdigit():
            raise serializers.ValidationError("Card number must contain digits only.")
        if len(value) not in range(13, 20):
            raise serializers.ValidationError("Card number length is invalid.")
        # Luhn validation
        digits = [int(x) for x in value]
        checksum = 0
        parity = len(digits) % 2
        for i, digit in enumerate(digits):
            if i % 2 == parity:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        if checksum % 10 != 0:
            raise serializers.ValidationError("Invalid card number.")
        return value

    def validate(self, attrs):
        expiry_month = attrs["expiry_month"]
        expiry_year = attrs["expiry_year"]
        if not 1 <= expiry_month <= 12:
            raise serializers.ValidationError({"expiry_month": "Must be between 1 and 12."})
        today = date.today()
        if expiry_year < today.year or (expiry_year == today.year and expiry_month < today.month):
            raise serializers.ValidationError({"expiry_year": "Card is expired."})
        return attrs

    def create(self, validated_data):
        card_number = validated_data.pop("card_number")
        validated_data.pop("cvv")  # deliberately discarded
        validated_data["user"] = self.context["request"].user
        validated_data["last4"] = card_number[-4:]
        validated_data["masked_card_number"] = "*" * (len(card_number) - 4) + card_number[-4:]
        return Card.objects.create(**validated_data)
