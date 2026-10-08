from django.conf import settings
from django.db import models

class Card(models.Model):
    class CardType(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        DEBIT = "DEBIT", "Debit"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cards")
    card_type = models.CharField(max_length=10, choices=CardType.choices)
    masked_card_number = models.CharField(max_length=19)
    last4 = models.CharField(max_length=4)
    card_holder_name = models.CharField(max_length=100)
    expiry_month = models.PositiveSmallIntegerField()
    expiry_year = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.card_type} {self.masked_card_number}"
