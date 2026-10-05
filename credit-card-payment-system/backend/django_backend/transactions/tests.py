from django.contrib.auth import get_user_model
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
