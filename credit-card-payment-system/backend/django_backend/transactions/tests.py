from django.contrib.auth import get_user_model
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from accounts.models import UserCreditProfile
from cards.models import Card
from transactions.models import Transaction
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import override_settings

User = get_user_model()

class TransactionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="txuser", password="StrongPass123!")
        self.card = Card.objects.create(
            user=self.user, card_type="CREDIT",
            masked_card_number="************1111", last4="1111",
            card_holder_name="Test", expiry_month=12, expiry_year=2030
        )
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_transaction_history(self):
        Transaction.objects.create(user=self.user, card=self.card, amount=100, reference="TX-TEST-1")
        response = self.client.get("/api/transactions/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_dashboard_summary_is_authenticated_and_returns_user_spending_metrics(self):
        self.client.credentials()
        self.assertEqual(self.client.get("/dashboard/summary").status_code, 401)
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        now = timezone.now()
        for index in range(1, 7):
            transaction = Transaction.objects.create(
                user=self.user,
                card=self.card,
                amount=10,
                status=Transaction.Status.SUCCESS,
                reference=f"TX-DASH-{index}",
            )
            created_at = now - timedelta(days=35) if index == 1 else now + timedelta(minutes=index)
            Transaction.objects.filter(pk=transaction.pk).update(created_at=created_at)
        debit_card = Card.objects.create(
            user=self.user,
            card_type="DEBIT",
            masked_card_number="************3333",
            last4="3333",
            card_holder_name="Test",
            expiry_month=12,
            expiry_year=2030,
        )
        debit_transaction = Transaction.objects.create(
            user=self.user,
            card=debit_card,
            amount=20,
            status=Transaction.Status.SUCCESS,
            reference="TX-DASH-DEBIT",
        )
        Transaction.objects.filter(pk=debit_transaction.pk).update(
            created_at=now - timedelta(days=36)
        )
        Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount=80,
            status=Transaction.Status.FAILED,
            reference="TX-DASH-FAILED",
        )
        Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount=90,
            status=Transaction.Status.PENDING,
            reference="TX-DASH-PENDING",
        )

        other_user = User.objects.create_user(
            username="other-tx-user",
            password="test-password",
        )
        other_card = Card.objects.create(
            user=other_user,
            card_type="CREDIT",
            masked_card_number="************2222",
            last4="2222",
            card_holder_name="Other",
            expiry_month=12,
            expiry_year=2030,
        )
        Transaction.objects.create(
            user=other_user,
            card=other_card,
            amount=500,
            status=Transaction.Status.SUCCESS,
            reference="TX-DASH-OTHER",
        )
        UserCreditProfile.objects.filter(user=self.user).update(
            credit_limit="100.00"
        )

        response = self.client.get("/dashboard/summary")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_transactions"], 9)
        self.assertEqual(response.data["total_amount_spent"], Decimal("250.00"))
        self.assertEqual(response.data["current_month_spending"], Decimal("50.00"))
        self.assertEqual(response.data["available_credit_limit"], Decimal("40.00"))
        self.assertEqual(
            [item["reference"] for item in response.data["last_5_transactions"]],
            [f"TX-DASH-{index}" for index in (6, 5, 4, 3, 2)],
        )

    def test_internal_dashboard_summary_requires_secret_and_returns_user_summary(self):
        secret = "test-internal-secret-key-long-enough"
        with override_settings(DJANGO_INTERNAL_SECRET=secret):
            unauthorized = self.client.get(
                f"/api/internal/transactions/dashboard/summary/?user_id={self.user.id}"
            )
            response = self.client.get(
                f"/api/internal/transactions/dashboard/summary/?user_id={self.user.id}",
                HTTP_X_INTERNAL_SECRET=secret,
            )

        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_transactions"], 0)
        self.assertEqual(response.data["last_5_transactions"], [])

    def test_admin_summary_includes_daily_payments(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        Transaction.objects.create(user=self.user, card=self.card, amount=100, reference="TX-DAILY-1")

        response = self.client.get("/api/admin/summary/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["daily"]["total_transactions"], 1)
        self.assertEqual(response.data["daily"]["pending"], 1)

    def test_internal_transaction_endpoint_rejects_missing_or_weak_secret(self):
        for secret in ("", "short-secret"):
            with self.subTest(secret_length=len(secret)), override_settings(
                DJANGO_INTERNAL_SECRET=secret
            ):
                response = self.client.post(
                    "/api/internal/transactions/create/",
                    {
                        "user_id": self.user.id,
                        "card_id": self.card.id,
                        "amount": "25.00",
                        "reference": "TX-NO-SECRET",
                    },
                    format="json",
                )

                self.assertEqual(response.status_code, 401)

    def test_internal_transaction_cannot_change_finalized_status(self):
        transaction = Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount=100,
            reference="TX-FINALIZED",
            status=Transaction.Status.SUCCESS,
        )

        with override_settings(DJANGO_INTERNAL_SECRET="test-internal-secret-key-long-enough"):
            response = self.client.patch(
                f"/api/internal/transactions/{transaction.reference}/",
                {"status": Transaction.Status.FAILED, "failure_reason": "retry"},
                format="json",
                HTTP_X_INTERNAL_SECRET="test-internal-secret-key-long-enough",
            )

        self.assertEqual(response.status_code, 409)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, Transaction.Status.SUCCESS)
