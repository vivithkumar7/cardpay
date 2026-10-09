from django.conf import settings
from django.db import models
from cards.models import Card


class Transaction(models.Model):
    class Category(models.TextChoices):
        FOOD = "FOOD", "Food & dining"
        SHOPPING = "SHOPPING", "Shopping"
        TRAVEL = "TRAVEL", "Travel"
        BILLS = "BILLS", "Bills & utilities"
        HEALTHCARE = "HEALTHCARE", "Healthcare"
        ENTERTAINMENT = "ENTERTAINMENT", "Entertainment"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    class FraudStatus(models.TextChoices):
        CLEAR = "CLEAR", "Clear"
        FLAGGED = "FLAGGED", "Flagged"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    card = models.ForeignKey(Card, on_delete=models.PROTECT, related_name="transactions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reference = models.CharField(max_length=40, unique=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    fraud_status = models.CharField(
        max_length=10,
        choices=FraudStatus.choices,
        default=FraudStatus.CLEAR,
    )
    location_fingerprint = models.CharField(max_length=64, blank=True)
    device_fingerprint = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("view_all_transactions", "Can view all transactions"),
            ("view_analytics", "Can view transaction analytics"),
        ]
        indexes = [
            models.Index(
                fields=["user", "-created_at", "-id"],
                name="tx_user_created_idx",
            ),
            models.Index(
                fields=["user", "status", "-created_at"],
                name="tx_user_status_date_idx",
            ),
            models.Index(fields=["user", "amount"], name="tx_user_amount_idx"),
            models.Index(
                fields=["fraud_status", "created_at"],
                name="tx_fraud_created_idx",
            ),
        ]

    def __str__(self):
        return self.reference


class FraudAlert(models.Model):
    class ReviewStatus(models.TextChoices):
        OPEN = "OPEN", "Open"
        REVIEWED = "REVIEWED", "Reviewed"
        FALSE_POSITIVE = "FALSE_POSITIVE", "False positive"

    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name="fraud_alert",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fraud_alerts",
    )
    rule_codes = models.JSONField(default=list)
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.OPEN,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_fraud_alerts",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-detected_at"]
        permissions = [
            ("review_fraud_alerts", "Can review fraud alerts"),
        ]
        indexes = [
            models.Index(
                fields=["review_status", "detected_at"],
                name="fraud_review_detected_idx",
            ),
        ]

    def __str__(self):
        return f"Fraud alert for {self.transaction.reference}"
