import csv
import secrets
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.http import HttpResponse
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import UserCreditProfile
from .models import Transaction
from .serializers import TransactionSerializer

def _has_valid_internal_secret(request):
    expected_secret = settings.DJANGO_INTERNAL_SECRET
    provided_secret = request.headers.get("X-Internal-Secret", "")
    return len(expected_secret) >= 32 and secrets.compare_digest(provided_secret, expected_secret)

class TransactionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        qs = Transaction.objects.filter(user=self.request.user).select_related("card")
        status_value = self.request.query_params.get("status")
        min_amount = self.request.query_params.get("min_amount")
        max_amount = self.request.query_params.get("max_amount")
        from_date = self.request.query_params.get("from_date")
        to_date = self.request.query_params.get("to_date")

        if status_value:
            qs = qs.filter(status=status_value.upper())
        if min_amount:
            qs = qs.filter(amount__gte=min_amount)
        if max_amount:
            qs = qs.filter(amount__lte=max_amount)
        if from_date:
            qs = qs.filter(created_at__date__gte=from_date)
        if to_date:
            qs = qs.filter(created_at__date__lte=to_date)
        return qs


class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(_dashboard_summary_data(request.user))


def _dashboard_summary_data(user):
    user_transactions = Transaction.objects.filter(user=user)
    successful_transactions = user_transactions.filter(
        status=Transaction.Status.SUCCESS
    )
    spending = user_transactions.aggregate(total=Sum("amount"))["total"]
    if spending is None:
        spending = Decimal("0.00")

    today = timezone.localdate()
    month_spending = successful_transactions.filter(
        created_at__year=today.year,
        created_at__month=today.month,
    ).aggregate(total=Sum("amount"))["total"]
    if month_spending is None:
        month_spending = Decimal("0.00")

    profile, _ = UserCreditProfile.objects.get_or_create(user=user)
    credit_spending = successful_transactions.filter(
        card__card_type="CREDIT"
    ).aggregate(total=Sum("amount"))["total"]
    if credit_spending is None:
        credit_spending = Decimal("0.00")
    available_credit_limit = max(
        profile.credit_limit - credit_spending, Decimal("0.00")
    )
    last_transactions = user_transactions.select_related("card").order_by(
        "-created_at", "-pk"
    )[:5]

    return {
        "total_transactions": user_transactions.count(),
        "total_amount_spent": spending,
        "current_month_spending": month_spending,
        "available_credit_limit": available_credit_limit,
        "last_5_transactions": TransactionSerializer(
            last_transactions, many=True
        ).data,
    }


class InternalTransactionCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        if not _has_valid_internal_secret(request):
            return Response({"detail": "Unauthorized internal request."}, status=401)

        user_id = request.data.get("user_id")
        card_id = request.data.get("card_id")
        amount = request.data.get("amount")
        reference = request.data.get("reference")
        from django.contrib.auth import get_user_model
        from cards.models import Card
        User = get_user_model()

        try:
            user = User.objects.get(id=user_id)
            card = Card.objects.get(id=card_id, user=user)
            if float(amount) <= 0:
                raise ValueError()
        except Exception:
            return Response({"detail": "Invalid user, card or amount."}, status=400)

        tx = Transaction.objects.create(
            user=user, card=card, amount=amount,
            reference=reference or f"TX-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        )
        return Response(TransactionSerializer(tx).data, status=201)


class InternalDashboardSummaryView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        if not _has_valid_internal_secret(request):
            return Response({"detail": "Unauthorized internal request."}, status=401)

        from django.contrib.auth import get_user_model

        user_id = request.query_params.get("user_id")
        try:
            user = get_user_model().objects.get(pk=user_id)
        except (get_user_model().DoesNotExist, ValueError, TypeError):
            return Response({"detail": "User not found."}, status=404)
        return Response(_dashboard_summary_data(user))


class InternalTransactionUpdateView(APIView):
    authentication_classes = []
    permission_classes = []

    def patch(self, request, reference):
        if not _has_valid_internal_secret(request):
            return Response({"detail": "Unauthorized internal request."}, status=401)
        try:
            tx = Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            return Response({"detail": "Transaction not found."}, status=404)
        status_value = request.data.get("status")
        final_statuses = (Transaction.Status.SUCCESS, Transaction.Status.FAILED)
        if status_value not in final_statuses:
            return Response({"detail": "Status must be SUCCESS or FAILED."}, status=400)

        updated = Transaction.objects.filter(
            pk=tx.pk,
            status=Transaction.Status.PENDING,
        ).update(
            status=status_value,
            failure_reason=request.data.get("failure_reason", ""),
            updated_at=timezone.now(),
        )
        if not updated:
            return Response({"detail": "Only pending transactions can be finalized."}, status=409)
        tx.refresh_from_db()
        return Response(TransactionSerializer(tx).data)

class TransactionExportView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        qs = Transaction.objects.select_related("user", "card").all()
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="transactions.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "User", "Amount", "Currency", "Status", "Reference", "Card", "Created At"])
        for tx in qs:
            writer.writerow([
                tx.id, tx.user.username, tx.amount, tx.currency, tx.status,
                tx.reference, tx.card.masked_card_number, tx.created_at.isoformat()
            ])
        return response

class AdminSummaryView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        data = Transaction.objects.values("status").annotate(
            count=Count("id"), total=Sum("amount")
        )
        today_transactions = Transaction.objects.filter(created_at__date=timezone.localdate())
        daily_data = today_transactions.values("status").annotate(
            count=Count("id"), total=Sum("amount")
        )
        return Response({
            "total_transactions": Transaction.objects.count(),
            "successful": next((x["count"] for x in data if x["status"] == "SUCCESS"), 0),
            "failed": next((x["count"] for x in data if x["status"] == "FAILED"), 0),
            "pending": next((x["count"] for x in data if x["status"] == "PENDING"), 0),
            "total_amount": sum((x["total"] or 0 for x in data), 0),
            "daily": {
                "date": timezone.localdate().isoformat(),
                "total_transactions": today_transactions.count(),
                "successful": next((x["count"] for x in daily_data if x["status"] == "SUCCESS"), 0),
                "failed": next((x["count"] for x in daily_data if x["status"] == "FAILED"), 0),
                "pending": next((x["count"] for x in daily_data if x["status"] == "PENDING"), 0),
                "total_amount": sum((x["total"] or 0 for x in daily_data), 0),
            },
        })
