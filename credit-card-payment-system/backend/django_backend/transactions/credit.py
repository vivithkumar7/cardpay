from decimal import Decimal

from django.db.models import Sum

from accounts.models import UserCreditProfile
from accounts.notifications import queue_account_email
from .models import Transaction


LOW_CREDIT_PERCENT = Decimal("0.10")


def available_credit_for(user, credit_limit=None):
    if credit_limit is None:
        profile, _ = UserCreditProfile.objects.get_or_create(user=user)
        credit_limit = profile.credit_limit
    spent = (
        Transaction.objects.filter(
            user=user,
            status=Transaction.Status.SUCCESS,
            card__card_type="CREDIT",
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )
    return max(credit_limit - spent, Decimal("0.00"))


def is_below_low_credit_threshold(available_credit, credit_limit):
    return credit_limit > 0 and available_credit < credit_limit * LOW_CREDIT_PERCENT


def notify_if_credit_fell_below_threshold(
    user,
    previous_available,
    previous_limit,
    current_available,
    current_limit,
):
    was_below = is_below_low_credit_threshold(previous_available, previous_limit)
    is_below = is_below_low_credit_threshold(current_available, current_limit)
    if is_below and not was_below:
        queue_account_email(
            user,
            "Available credit below 10%",
            (
                f"Your available credit is now {current_available:.2f}, below 10% "
                f"of your {current_limit:.2f} credit limit."
            ),
        )
