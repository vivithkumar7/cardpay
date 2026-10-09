import csv
import io
import logging
import re
import secrets
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from decimal import InvalidOperation

from django.conf import settings
from django.db import connection
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, permissions, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph
from accounts.models import UserCreditProfile
from accounts.notifications import queue_account_email
from accounts.role_permissions import (
    CanReviewFraudAlerts,
    CanViewAllTransactions,
    CanViewAnalytics,
    can_initiate_payments,
)
from audit.models import AdminLog
from .credit import available_credit_for, notify_if_credit_fell_below_threshold
from .fraud import create_transaction_with_fraud_check
from .models import FraudAlert, Transaction
from config.monitoring import get_health_snapshot
from .serializers import (
    FraudAlertReviewSerializer,
    FraudAlertSerializer,
    TransactionSerializer,
)

logger = logging.getLogger(__name__)


class TransactionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class FraudAlertPagination(PageNumberPagination):
    page_size = 25


TRANSACTION_ORDERINGS = {
    "created_at": "created_at",
    "amount": "amount",
    "status": "status",
    "reference": "reference",
    "category": "category",
}


def _has_valid_internal_secret(request):
    expected_secret = settings.DJANGO_INTERNAL_SECRET
    provided_secret = request.headers.get("X-Internal-Secret", "")
    return len(expected_secret) >= 32 and secrets.compare_digest(provided_secret, expected_secret)


def _month_start(month, offset=0):
    month_index = month.year * 12 + month.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def _day_start(day):
    return timezone.make_aware(datetime.combine(day, time.min))


def _money_string(amount):
    return str(Decimal(amount).quantize(Decimal("0.01")))


class TransactionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination

    def get_queryset(self):
        qs = Transaction.objects.filter(user=self.request.user).select_related("card")
        status_value = self.request.query_params.get("status")
        min_amount = self.request.query_params.get("min_amount")
        max_amount = self.request.query_params.get("max_amount")
        from_date = self.request.query_params.get("from_date")
        to_date = self.request.query_params.get("to_date")
        fraud_status = self.request.query_params.get("fraud_status")
        card_search = self.request.query_params.get("card_search", "").strip()
        ordering = self.request.query_params.get("ordering", "-created_at")

        if status_value:
            status_value = status_value.upper()
            if status_value not in Transaction.Status.values:
                raise serializers.ValidationError({"status": "Unknown transaction status."})
            qs = qs.filter(status=status_value)
        if min_amount:
            qs = qs.filter(amount__gte=self._amount("min_amount", min_amount))
        if max_amount:
            qs = qs.filter(amount__lte=self._amount("max_amount", max_amount))
        if min_amount and max_amount and Decimal(min_amount) > Decimal(max_amount):
            raise serializers.ValidationError(
                {"max_amount": "Maximum amount must be at least the minimum amount."}
            )
        parsed_from_date = self._date("from_date", from_date) if from_date else None
        parsed_to_date = self._date("to_date", to_date) if to_date else None
        if parsed_from_date:
            qs = qs.filter(created_at__gte=_day_start(parsed_from_date))
        if parsed_to_date:
            qs = qs.filter(
                created_at__lt=_day_start(parsed_to_date + timedelta(days=1))
            )
        if parsed_from_date and parsed_to_date and parsed_from_date > parsed_to_date:
            raise serializers.ValidationError(
                {"to_date": "End date must be on or after the start date."}
            )
        if fraud_status:
            fraud_status = fraud_status.upper()
            if fraud_status not in Transaction.FraudStatus.values:
                raise serializers.ValidationError({"fraud_status": "Unknown fraud status."})
            qs = qs.filter(fraud_status=fraud_status)
        if card_search:
            digits = re.sub(r"\D", "", card_search)
            if digits:
                lookup = "card__last4" if len(digits) >= 4 else "card__last4__icontains"
                qs = qs.filter(**{lookup: digits[-4:]})
            else:
                qs = qs.filter(card__masked_card_number__icontains=card_search)

        descending = ordering.startswith("-")
        ordering_key = ordering[1:] if descending else ordering
        if ordering_key not in TRANSACTION_ORDERINGS:
            raise serializers.ValidationError(
                {"ordering": "Unsupported ordering field."}
            )
        ordering_field = TRANSACTION_ORDERINGS[ordering_key]
        if descending:
            ordering_field = f"-{ordering_field}"
        return qs.order_by(ordering_field, "-pk")

    @staticmethod
    def _amount(field_name, value):
        try:
            amount = serializers.DecimalField(
                max_digits=12,
                decimal_places=2,
            ).run_validation(value)
        except serializers.ValidationError as error:
            raise serializers.ValidationError({field_name: error.detail})
        if not amount.is_finite() or amount < 0:
            raise serializers.ValidationError(
                {field_name: "Amount must be a finite, non-negative value."}
            )
        return amount

    @staticmethod
    def _date(field_name, value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise serializers.ValidationError(
                {field_name: "Enter a date in YYYY-MM-DD format."}
            )


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
        created_at__gte=_day_start(_month_start(today)),
        created_at__lt=_day_start(_month_start(today, 1)),
    ).aggregate(total=Sum("amount"))["total"]
    if month_spending is None:
        month_spending = Decimal("0.00")

    profile, _ = UserCreditProfile.objects.get_or_create(user=user)
    available_credit_limit = available_credit_for(user, profile.credit_limit)
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


class CardUsageAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        current_month = date(today.year, today.month, 1)
        first_month = _month_start(current_month, -5)
        analytics_start = _day_start(first_month)
        analytics_end = _day_start(today + timedelta(days=1))
        monthly_transactions = Transaction.objects.filter(
            user=user,
            status=Transaction.Status.SUCCESS,
            created_at__gte=analytics_start,
            created_at__lt=analytics_end,
        )
        monthly_spending = {}
        monthly_summary = []
        for month_offset in range(6):
            month = _month_start(first_month, month_offset)
            month_key = month.strftime("%Y-%m")
            next_month = _month_start(month, 1)
            total = monthly_transactions.filter(
                created_at__gte=_day_start(month),
                created_at__lt=_day_start(next_month),
            ).aggregate(total=Sum("amount"))["total"]
            monthly_spending[month_key] = total or Decimal("0.00")
            monthly_summary.append(
                {
                    "month": month_key,
                    "spending": _money_string(
                        monthly_spending.get(month_key, Decimal("0.00"))
                    ),
                }
            )

        category_rows = (
            Transaction.objects.filter(
                user=user,
                status=Transaction.Status.SUCCESS,
                created_at__gte=analytics_start,
                created_at__lt=analytics_end,
            )
            .values("category")
            .annotate(total=Sum("amount"))
            .order_by("-total", "category")
        )
        category_spending = [
            {
                "category": row["category"],
                "label": Transaction.Category(row["category"]).label,
                "spending": _money_string(row["total"]),
            }
            for row in category_rows
        ]
        profile, _ = UserCreditProfile.objects.get_or_create(user=user)
        credit_spending = (
            Transaction.objects.filter(
                user=user,
                status=Transaction.Status.SUCCESS,
                card__card_type="CREDIT",
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        utilization = (
            credit_spending * Decimal("100") / profile.credit_limit
            if profile.credit_limit > 0
            else Decimal("0.00")
        )

        daily_summary = {}
        for day_offset in reversed(range(7)):
            day = today - timedelta(days=day_offset)
            daily_rows = (
                Transaction.objects.filter(
                    user=user,
                    created_at__gte=_day_start(day),
                    created_at__lt=_day_start(day + timedelta(days=1)),
                )
                .values("status")
                .annotate(count=Count("id"))
            )
            daily_summary[day.isoformat()] = {
                status: next(
                    (row["count"] for row in daily_rows if row["status"] == status),
                    0,
                )
                for status in Transaction.Status.values
            }
        status_counts = {
            row["status"]: row["count"]
            for row in Transaction.objects.filter(user=user)
            .values("status")
            .annotate(count=Count("id"))
        }

        return Response(
            {
                "monthly_spending": monthly_summary,
                "category_spending": category_spending,
                "credit_limit": _money_string(profile.credit_limit),
                "credit_spending": _money_string(credit_spending),
                "credit_utilization_percentage": str(
                    utilization.quantize(Decimal("0.01"))
                ),
                "transaction_status_counts": {
                    status: status_counts.get(status, 0)
                    for status in Transaction.Status.values
                },
                "daily_activity": [
                    {
                        "date": (today - timedelta(days=day_offset)).isoformat(),
                        **daily_summary.get(
                            (today - timedelta(days=day_offset)).isoformat(),
                            {"SUCCESS": 0, "FAILED": 0, "PENDING": 0},
                        ),
                    }
                    for day_offset in reversed(range(7))
                ],
            }
        )


class InternalTransactionCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        if not _has_valid_internal_secret(request):
            return Response({"detail": "Unauthorized internal request."}, status=401)

        user_id = request.data.get("user_id")
        card_id = request.data.get("card_id")
        amount = request.data.get("amount")
        category = request.data.get("category", Transaction.Category.OTHER)
        reference = request.data.get("reference")
        source_ip = request.data.get("source_ip", "")
        device_id = request.data.get("device_id", "")
        from django.contrib.auth import get_user_model
        from cards.models import Card
        User = get_user_model()

        try:
            user = User.objects.get(id=user_id)
            if not can_initiate_payments(user):
                return Response(
                    {"detail": "This role cannot initiate payments."},
                    status=403,
                )
            card = Card.objects.get(id=card_id, user=user)
            if not card.is_active:
                return Response({"detail": "This card is inactive."}, status=409)
            amount = Decimal(str(amount))
            if (
                not amount.is_finite()
                or amount <= 0
                or amount.as_tuple().exponent < -2
                or not isinstance(device_id, str)
                or len(device_id) > 128
                or not isinstance(source_ip, str)
                or category not in Transaction.Category.values
            ):
                raise ValueError()
        except (
            get_user_model().DoesNotExist,
            Card.DoesNotExist,
            InvalidOperation,
            ValueError,
            TypeError,
        ):
            return Response({"detail": "Invalid user, card or amount."}, status=400)

        tx, _ = create_transaction_with_fraud_check(
            user=user,
            card=card,
            amount=amount,
            reference=reference or f"TX-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            category=category,
            source_ip=source_ip,
            device_id=device_id,
        )
        tx.refresh_from_db()
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

        profile, _ = UserCreditProfile.objects.get_or_create(user=tx.user)
        previous_limit = profile.credit_limit
        previous_available = available_credit_for(tx.user, previous_limit)
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
        if status_value == Transaction.Status.SUCCESS and tx.card.card_type == "CREDIT":
            notify_if_credit_fell_below_threshold(
                tx.user,
                previous_available,
                previous_limit,
                available_credit_for(tx.user, previous_limit),
                previous_limit,
            )
        queue_account_email(
            tx.user,
            (
                f"High-value payment {tx.status.lower()}"
                if tx.amount > Decimal("5000.00")
                else f"Payment {tx.status.lower()}"
            ),
            (
                f"Payment {tx.reference} for {tx.currency} {tx.amount} was "
                f"{tx.status.lower()}. Card ending in {tx.card.last4}."
                + (
                    " This transaction exceeded the ₹5,000 alert threshold."
                    if tx.amount > Decimal("5000.00")
                    else ""
                )
            ),
        )
        return Response(TransactionSerializer(tx).data)

class TransactionExportView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanViewAllTransactions]

    def get(self, request):
        qs = Transaction.objects.select_related("user", "card").all()
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="transactions.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "ID",
                "User",
                "Amount",
                "Currency",
                "Category",
                "Status",
                "Fraud Status",
                "Reference",
                "Card",
                "Created At",
            ]
        )
        for tx in qs:
            writer.writerow([
                tx.id, tx.user.username, tx.amount, tx.currency, tx.category, tx.status,
                tx.fraud_status,
                tx.reference, tx.card.masked_card_number, tx.created_at.isoformat()
            ])
        return response

class AdminSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanViewAnalytics]

    def get(self, request):
        data = Transaction.objects.values("status").annotate(
            count=Count("id"), total=Sum("amount")
        )
        today = timezone.localdate()
        today_transactions = Transaction.objects.filter(
            created_at__gte=_day_start(today),
            created_at__lt=_day_start(today + timedelta(days=1)),
        )
        daily_data = today_transactions.values("status").annotate(
            count=Count("id"), total=Sum("amount")
        )
        return Response({
            "total_transactions": Transaction.objects.count(),
            "flagged_transactions": Transaction.objects.filter(
                fraud_status=Transaction.FraudStatus.FLAGGED
            ).count(),
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


class SystemHealthView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanViewAnalytics]

    def get(self, request):
        database_healthy = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            database_healthy = False
            logger.exception("System health database check failed.")

        return Response(
            {
                "status": "healthy" if database_healthy else "degraded",
                "checked_at": timezone.now(),
                "database": "healthy" if database_healthy else "unavailable",
                "monitoring_scope": "This application process",
                **get_health_snapshot(),
            },
            status=200 if database_healthy else 503,
        )


class AnalyticsExportView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanViewAnalytics]

    def get(self, request):
        export_format = request.query_params.get("file_format", "csv").lower()
        if export_format not in {"csv", "pdf"}:
            return Response(
                {"detail": "Format must be csv or pdf."},
                status=400,
            )

        today = timezone.localdate()
        current_month = _month_start(today)
        first_month = _month_start(current_month, -5)
        successful = Transaction.objects.filter(
            status=Transaction.Status.SUCCESS,
        )
        total_spending = successful.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        category_rows = successful.values("category").annotate(
            total=Sum("amount")
        ).order_by("-total", "category")
        monthly_rows = []
        for offset in range(6):
            month = _month_start(first_month, offset)
            month_total = successful.filter(
                created_at__gte=_day_start(month),
                created_at__lt=_day_start(_month_start(month, 1)),
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            monthly_rows.append((month.strftime("%Y-%m"), month_total))

        report_rows = [
            ("Summary", "Total transactions", Transaction.objects.count()),
            ("Summary", "Successful transactions", successful.count()),
            ("Summary", "Total successful spending (INR)", total_spending),
        ]
        report_rows.extend(
            (
                "Category",
                Transaction.Category(row["category"]).label,
                row["total"],
            )
            for row in category_rows
        )
        report_rows.extend(
            ("Monthly spending (INR)", month, amount)
            for month, amount in monthly_rows
        )

        if export_format == "csv":
            response = HttpResponse(content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = (
                'attachment; filename="analytics-summary.csv"'
            )
            writer = csv.writer(response)
            writer.writerow(["Report section", "Metric", "Value"])
            writer.writerows(report_rows)
            return response

        output = io.BytesIO()
        document = SimpleDocTemplate(
            output,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
        )
        styles = getSampleStyleSheet()
        content = [
            Paragraph("PaySecure analytics summary", styles["Title"]),
            Paragraph(f"Generated {timezone.localtime().strftime('%Y-%m-%d %H:%M %Z')}", styles["Normal"]),
            Spacer(1, 16),
        ]
        table = Table(
            [["Report section", "Metric", "Value"]]
            + [[str(value) for value in row] for row in report_rows],
            repeatRows=1,
            colWidths=[135, 250, 115],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#174b40")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d5ddd6")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f1")]),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        content.append(table)
        document.build(content)
        response = HttpResponse(output.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = (
            'attachment; filename="analytics-summary.pdf"'
        )
        return response


class FraudAlertListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, CanViewAnalytics]
    serializer_class = FraudAlertSerializer
    pagination_class = FraudAlertPagination

    def get_queryset(self):
        queryset = FraudAlert.objects.select_related(
            "transaction",
            "transaction__card",
            "user",
            "reviewed_by",
        )
        review_status = self.request.query_params.get("review_status")
        if review_status:
            queryset = queryset.filter(review_status=review_status.upper())
        return queryset


class FraudAlertReviewView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, CanReviewFraudAlerts]
    serializer_class = FraudAlertReviewSerializer
    queryset = FraudAlert.objects.all()
    http_method_names = ["patch", "options"]

    def perform_update(self, serializer):
        alert = serializer.instance
        previous_status = alert.review_status
        updated = serializer.save(
            reviewed_by=self.request.user,
            reviewed_at=timezone.now(),
        )
        AdminLog.objects.create(
            admin_user=self.request.user,
            action="fraud_alert_reviewed",
            details=(
                f"Fraud alert for transaction {updated.transaction.reference} "
                f"was marked {updated.review_status.lower()}."
            ),
            target_type="transaction",
            target_id=str(updated.transaction_id),
            changes={
                "fraud_review_status": {
                    "before": previous_status,
                    "after": updated.review_status,
                }
            },
        )
