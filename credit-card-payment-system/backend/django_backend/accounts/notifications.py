import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

logger = logging.getLogger(__name__)


def queue_account_email(user, subject, message):
    if not user.email:
        logger.info("Skipped %s email for user id=%s: no email address.", subject, user.pk)
        return

    transaction.on_commit(
        lambda: send_account_email(user.pk, user.email, subject, message)
    )


def send_account_email(user_id, email, subject, message):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except (OSError, SMTPException):
        logger.exception(
            "Email delivery failed for user id=%s, event=%s.", user_id, subject
        )
