from decimal import Decimal

from django.conf import settings
from django.db import models


class UserCreditProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="credit_profile",
    )
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    def __str__(self):
        return f"Credit profile for {self.user}"
