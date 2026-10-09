from django.db import transaction
from django.db.models import ProtectedError
from rest_framework import filters, generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.role_permissions import CanManageCards, CanViewAllCards
from accounts.models import UserCreditProfile
from accounts.notifications import queue_account_email
from audit.models import AdminLog
from transactions.credit import (
    available_credit_for,
    notify_if_credit_fell_below_threshold,
)
from transactions.models import Transaction

from .admin_serializers import AdminCardSerializer
from .admin_serializers import AdminCardActivitySerializer
from .models import Card


class AdminCardActivityPagination(PageNumberPagination):
    page_size = 25
    max_page_size = 100


class AdminCardListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, CanViewAllCards]
    serializer_class = AdminCardSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "user__username",
        "user__email",
        "last4",
        "masked_card_number",
        "card_holder_name",
    ]
    queryset = Card.objects.select_related("user", "user__credit_profile").order_by(
        "-created_at", "-pk"
    )


class AdminCardActivityView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, CanViewAllCards]
    serializer_class = AdminCardActivitySerializer
    pagination_class = AdminCardActivityPagination

    def get_queryset(self):
        return (
            Transaction.objects.filter(card_id=self.kwargs["pk"])
            .select_related("card")
            .order_by("-created_at", "-pk")
        )

    def list(self, request, *args, **kwargs):
        if not Card.objects.filter(pk=self.kwargs["pk"]).exists():
            return Response(
                {"detail": "Card not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return super().list(request, *args, **kwargs)


class AdminCardDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, CanManageCards]
    serializer_class = AdminCardSerializer
    queryset = Card.objects.select_related("user", "user__credit_profile")
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def perform_update(self, serializer):
        card = self.get_object()
        previous_active = card.is_active
        profile, _ = UserCreditProfile.objects.get_or_create(user=card.user)
        previous_limit = profile.credit_limit
        previous_available = available_credit_for(card.user, previous_limit)
        updated = serializer.save()
        updated.user.refresh_from_db()
        updated_profile, _ = UserCreditProfile.objects.get_or_create(user=updated.user)
        updated_profile.refresh_from_db()
        if previous_active != updated.is_active:
            state = "unblocked" if updated.is_active else "blocked"
            AdminLog.objects.create(
                admin_user=self.request.user,
                action=f"card_{state}",
                details=(
                    f"Card id={updated.pk} (**** {updated.last4}) for "
                    f"{updated.user.get_username()} was {state}."
                ),
                target_type="card",
                target_id=str(updated.pk),
                changes={"is_active": {
                    "before": previous_active,
                    "after": updated.is_active,
                }},
            )
            queue_account_email(
                updated.user,
                f"Payment card {state}",
                f"Your card **** {updated.last4} has been {state} by PaySecure support."
                + (
                    " Payments with this card are now declined."
                    if not updated.is_active
                    else " Payments with this card are enabled again."
                ),
            )
        if previous_limit != updated_profile.credit_limit:
            AdminLog.objects.create(
                admin_user=self.request.user,
                action="credit_limit_updated",
                details=(
                    f"Credit limit for {updated.user.get_username()} changed "
                    f"from {previous_limit:.2f} to "
                    f"{updated_profile.credit_limit:.2f}."
                ),
                target_type="user_credit_profile",
                target_id=str(updated_profile.pk),
                changes={"credit_limit": {
                    "before": str(previous_limit),
                    "after": str(updated_profile.credit_limit),
                }},
            )
            queue_account_email(
                updated.user,
                "Account credit limit updated",
                "Your account credit limit was updated by PaySecure support.",
            )
            notify_if_credit_fell_below_threshold(
                updated.user,
                previous_available,
                previous_limit,
                available_credit_for(updated.user, updated_profile.credit_limit),
                updated_profile.credit_limit,
            )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        card = self.get_object()
        if Transaction.objects.filter(card=card).exists():
            return Response(
                {"detail": "A card with transaction history cannot be removed."},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            with transaction.atomic():
                card.delete()
        except ProtectedError:
            return Response(
                {"detail": "A card with transaction history cannot be removed."},
                status=status.HTTP_409_CONFLICT,
            )
        AdminLog.objects.create(
            admin_user=request.user,
            action="card_removed",
            details=(
                f"Card id={card.pk} (**** {card.last4}) for "
                f"{card.user.get_username()} was removed."
            ),
            target_type="card",
            target_id=str(card.pk),
            changes={"deleted": {"before": False, "after": True}},
        )
        queue_account_email(
            card.user,
            "Payment card removed",
            f"Your card **** {card.last4} was removed by PaySecure support.",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
