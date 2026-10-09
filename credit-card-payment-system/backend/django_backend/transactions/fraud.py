import logging
from datetime import timedelta
from decimal import Decimal
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils.crypto import salted_hmac

from .models import FraudAlert, Transaction

logger = logging.getLogger(__name__)

FRAUD_WINDOW = timedelta(minutes=10)
HIGH_VALUE_THRESHOLD = Decimal("5000.00")
HIGH_VALUE_TRANSACTION_LIMIT = 3


def _fingerprint(value, salt):
    if not value:
        return ""
    return salted_hmac(salt, value, secret=settings.SECRET_KEY).hexdigest()


def create_transaction_with_fraud_check(
    *,
    user,
    card,
    amount,
    reference,
    category=Transaction.Category.OTHER,
    source_ip="",
    device_id="",
):
    with transaction.atomic():
        # Serializing per-user attempts prevents concurrent payments from
        # overlooking each other when applying the velocity rules.
        user = get_user_model().objects.select_for_update().get(pk=user.pk)
        location_fingerprint = _fingerprint(source_ip, "fraud-location")
        device_fingerprint = _fingerprint(device_id, "fraud-device")
        payment = Transaction.objects.create(
            user=user,
            card=card,
            amount=amount,
            reference=reference,
            category=category,
            location_fingerprint=location_fingerprint,
            device_fingerprint=device_fingerprint,
        )

        recent = Transaction.objects.filter(
            user=user,
            created_at__gte=payment.created_at - FRAUD_WINDOW,
            created_at__lte=payment.created_at,
        )
        prior_attempts = recent.exclude(pk=payment.pk)
        rules = []
        if amount >= HIGH_VALUE_THRESHOLD:
            high_value_count = recent.filter(
                amount__gte=HIGH_VALUE_THRESHOLD
            ).count()
            if high_value_count >= HIGH_VALUE_TRANSACTION_LIMIT:
                rules.append("repeated_high_value_transactions")

        if location_fingerprint and prior_attempts.exclude(
            location_fingerprint=""
        ).exclude(location_fingerprint=location_fingerprint).exists():
            rules.append("rapid_location_change")
        if device_fingerprint and prior_attempts.exclude(
            device_fingerprint=""
        ).exclude(device_fingerprint=device_fingerprint).exists():
            rules.append("rapid_device_change")

        if rules:
            payment.fraud_status = Transaction.FraudStatus.FLAGGED
            payment.save(update_fields=["fraud_status"])
            alert = FraudAlert.objects.create(
                transaction=payment,
                user=user,
                rule_codes=rules,
            )
            transaction.on_commit(
                lambda: send_fraud_alert_emails(
                    user_id=user.pk,
                    reference=payment.reference,
                    amount=payment.amount,
                    last4=card.last4,
                    rule_codes=rules,
                )
            )
            return payment, alert

    return payment, None


def send_fraud_alert_emails(*, user_id, reference, amount, last4, rule_codes):
    user = get_user_model().objects.filter(pk=user_id).first()
    if user is None:
        logger.error(
            "Skipped fraud notification for missing user id=%s, transaction=%s.",
            user_id,
            reference,
        )
        return

    recipients = set()
    if user.email:
        recipients.add(user.email)
    operations_users = get_user_model().objects.filter(
        is_active=True,
        email__gt="",
    ).filter(
        models.Q(is_staff=True)
        | models.Q(groups__name__in=("Admin", "Support"))
    ).values_list("email", flat=True)
    recipients.update(operations_users)

    if not recipients:
        logger.info(
            "Skipped fraud notification for transaction=%s: no recipients.",
            reference,
        )
        return

    subject = f"Suspicious payment activity detected: {reference}"
    message = (
        f"Transaction {reference} for INR {amount} using card ending "
        f"in {last4} was flagged for review.\n"
        f"Detection rules: {', '.join(rule_codes)}."
    )
    for recipient in recipients:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
        except (OSError, SMTPException):
            logger.exception(
                "Fraud notification delivery failed for transaction=%s.",
                reference,
            )
