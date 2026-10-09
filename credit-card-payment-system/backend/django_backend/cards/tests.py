from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import UserCreditProfile
from audit.models import AdminLog
from transactions.models import Transaction

from .models import Card

User = get_user_model()

class CardTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="carduser", password="StrongPass123!")
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="PaySecure <no-reply@example.com>",
    )
    def test_card_is_masked_cvv_not_stored_and_addition_is_notified(self):
        mail.outbox.clear()
        self.user.email = "carduser@example.com"
        self.user.save(update_fields=["email"])
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/api/cards/", {
                "card_type": "CREDIT",
                "card_holder_name": "Test User",
                "expiry_month": 12,
                "expiry_year": 2030,
                "card_number": "4111111111111111",
                "cvv": "123"
            }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["last4"], "1111")
        self.assertNotIn("cvv", response.data)
        self.assertEqual(response.data["masked_card_number"], "************1111")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("1111", mail.outbox[0].body)
        self.assertNotIn("4111111111111111", mail.outbox[0].body)

    def test_inactive_card_cannot_start_a_payment(self):
        card = Card.objects.create(
            user=self.user,
            card_type="CREDIT",
            masked_card_number="************1111",
            last4="1111",
            card_holder_name="Test",
            expiry_month=12,
            expiry_year=2030,
            is_active=False,
        )
        secret = "test-internal-secret-key-long-enough"

        with override_settings(DJANGO_INTERNAL_SECRET=secret):
            response = self.client.post(
                "/api/internal/transactions/create/",
                {
                    "user_id": self.user.id,
                    "card_id": card.id,
                    "amount": "25.00",
                    "reference": "TX-INACTIVE-CARD",
                },
                format="json",
                HTTP_X_INTERNAL_SECRET=secret,
            )

        self.assertEqual(response.status_code, 409)
        self.assertFalse(Transaction.objects.filter(reference="TX-INACTIVE-CARD").exists())

    def test_admin_can_review_update_and_remove_cards_only_with_staff_access(self):
        card = Card.objects.create(
            user=self.user,
            card_type="CREDIT",
            masked_card_number="************1111",
            last4="1111",
            card_holder_name="Test",
            expiry_month=12,
            expiry_year=2030,
        )
        self.assertEqual(self.client.get("/api/admin/cards/").status_code, 403)

        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        response = self.client.get("/api/admin/cards/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["masked_card_number"], "************1111")
        self.assertNotIn("card_number", response.data[0])
        search = self.client.get("/api/admin/cards/?search=1111")
        self.assertEqual(search.status_code, 200)
        self.assertEqual([item["id"] for item in search.data], [card.id])
        no_match = self.client.get("/api/admin/cards/?search=not-a-customer")
        self.assertEqual(no_match.status_code, 200)
        self.assertEqual(no_match.data, [])

        update = self.client.patch(
            f"/api/admin/cards/{card.id}/",
            {"is_active": False, "credit_limit": "2500.00"},
            format="json",
        )
        self.assertEqual(update.status_code, 200)
        self.assertFalse(update.data["is_active"])
        self.assertEqual(
            UserCreditProfile.objects.get(user=self.user).credit_limit,
            Decimal("2500.00"),
        )
        self.assertTrue(
            AdminLog.objects.filter(
                admin_user=self.user,
                action="card_blocked",
                details__contains="**** 1111",
            ).exists()
        )
        self.assertTrue(
            AdminLog.objects.filter(
                admin_user=self.user,
                action="credit_limit_updated",
                details__contains="2500.00",
                target_type="user_credit_profile",
                changes__credit_limit__before="0.00",
                changes__credit_limit__after="2500.00",
            ).exists()
        )

        delete = self.client.delete(f"/api/admin/cards/{card.id}/")
        self.assertEqual(delete.status_code, 204)
        self.assertFalse(Card.objects.filter(pk=card.pk).exists())
        self.assertTrue(
            AdminLog.objects.filter(
                admin_user=self.user,
                action="card_removed",
                details__contains="**** 1111",
                target_type="card",
            ).exists()
        )

    def test_support_can_read_cards_and_only_block_or_unblock(self):
        self.user.groups.add(Group.objects.get(name="Support"))
        card = Card.objects.create(
            user=self.user,
            card_type="CREDIT",
            masked_card_number="************1111",
            last4="1111",
            card_holder_name="Test",
            expiry_month=12,
            expiry_year=2030,
        )

        self.assertEqual(self.client.get("/api/admin/cards/").status_code, 200)
        self.assertEqual(
            self.client.get(f"/api/admin/cards/{card.id}/").status_code, 200
        )
        self.assertEqual(
            self.client.post(
                "/api/cards/",
                {
                    "card_type": "CREDIT",
                    "card_holder_name": "Test",
                    "expiry_month": 12,
                    "expiry_year": 2030,
                    "card_number": "4111111111111111",
                    "cvv": "123",
                },
                format="json",
            ).status_code,
            403,
        )
        block = self.client.patch(
            f"/api/admin/cards/{card.id}/", {"is_active": False}, format="json"
        )
        self.assertEqual(block.status_code, 200)
        self.assertTrue(
            AdminLog.objects.filter(
                admin_user=self.user,
                action="card_blocked",
                target_type="card",
                target_id=str(card.id),
                changes__is_active__before=True,
                changes__is_active__after=False,
            ).exists()
        )
        limit_change = self.client.patch(
            f"/api/admin/cards/{card.id}/",
            {"credit_limit": "2500.00"},
            format="json",
        )
        self.assertEqual(limit_change.status_code, 403)
        self.assertEqual(
            self.client.delete(f"/api/admin/cards/{card.id}/").status_code, 403
        )
        self.assertEqual(
            self.client.delete(f"/api/cards/{card.id}/").status_code, 403
        )
        self.assertEqual(
            UserCreditProfile.objects.get(user=self.user).credit_limit,
            Decimal("0.00"),
        )
        self.assertFalse(
            AdminLog.objects.filter(
                admin_user=self.user, action="credit_limit_updated"
            ).exists()
        )

    def test_admin_group_can_manage_cards_without_staff_flag(self):
        self.user.groups.add(Group.objects.get(name="Admin"))
        card = Card.objects.create(
            user=self.user,
            card_type="CREDIT",
            masked_card_number="************1111",
            last4="1111",
            card_holder_name="Test",
            expiry_month=12,
            expiry_year=2030,
        )

        response = self.client.patch(
            f"/api/admin/cards/{card.id}/",
            {"credit_limit": "2500.00"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            UserCreditProfile.objects.get(user=self.user).credit_limit,
            Decimal("2500.00"),
        )

    def test_read_only_role_cannot_change_or_delete_cards(self):
        self.user.groups.add(Group.objects.get(name="Read-Only"))
        card = Card.objects.create(
            user=self.user,
            card_type="CREDIT",
            masked_card_number="************1111",
            last4="1111",
            card_holder_name="Test",
            expiry_month=12,
            expiry_year=2030,
        )

        self.assertEqual(self.client.get("/api/admin/cards/").status_code, 200)
        self.assertEqual(
            self.client.patch(
                f"/api/admin/cards/{card.id}/",
                {"is_active": False},
                format="json",
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.delete(f"/api/admin/cards/{card.id}/").status_code, 403
        )

    def test_admin_cannot_remove_a_card_with_transaction_history(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        card = Card.objects.create(
            user=self.user,
            card_type="CREDIT",
            masked_card_number="************1111",
            last4="1111",
            card_holder_name="Test",
            expiry_month=12,
            expiry_year=2030,
        )
        Transaction.objects.create(
            user=self.user, card=card, amount="10.00", reference="TX-PROTECTED-CARD"
        )

        response = self.client.delete(f"/api/admin/cards/{card.id}/")

        self.assertEqual(response.status_code, 409)
        self.assertTrue(Card.objects.filter(pk=card.pk).exists())

    def test_card_activity_requires_staff_and_is_limited_to_the_selected_card(self):
        card = Card.objects.create(
            user=self.user,
            card_type="CREDIT",
            masked_card_number="************1111",
            last4="1111",
            card_holder_name="Card Owner",
            expiry_month=12,
            expiry_year=2030,
        )
        Transaction.objects.create(
            user=self.user,
            card=card,
            amount="15.00",
            status=Transaction.Status.FAILED,
            reference="TX-OWN-CARD",
            failure_reason="Simulated failure.",
        )
        other_user = User.objects.create_user(
            username="different-card-owner", password="StrongPass123!"
        )
        other_card = Card.objects.create(
            user=other_user,
            card_type="DEBIT",
            masked_card_number="************2222",
            last4="2222",
            card_holder_name="Other Owner",
            expiry_month=11,
            expiry_year=2031,
        )
        Transaction.objects.create(
            user=other_user,
            card=other_card,
            amount="99.00",
            status=Transaction.Status.SUCCESS,
            reference="TX-OTHER-CARD",
        )

        self.client.credentials()
        self.assertEqual(
            self.client.get(f"/api/admin/cards/{card.id}/activity/").status_code, 401
        )
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(
            self.client.get(f"/api/admin/cards/{card.id}/activity/").status_code, 403
        )

        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(f"/api/admin/cards/{card.id}/activity/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["reference"], "TX-OWN-CARD")
        self.assertEqual(response.data["results"][0]["card_mask"], card.masked_card_number)
        self.assertNotIn("TX-OTHER-CARD", str(response.data))
        self.assertNotIn("card_number", response.data["results"][0])
        self.assertEqual(
            self.client.get("/api/admin/cards/999999/activity/").status_code, 404
        )

    def test_admin_card_list_contains_all_stored_non_sensitive_card_details(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        card = Card.objects.create(
            user=self.user,
            card_type="DEBIT",
            masked_card_number="************5555",
            last4="5555",
            card_holder_name="Stored Cardholder",
            expiry_month=3,
            expiry_year=2032,
            is_active=False,
        )
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get("/api/admin/cards/")

        self.assertEqual(response.status_code, 200)
        details = response.data[0]
        for field in (
            "id",
            "username",
            "email",
            "card_type",
            "masked_card_number",
            "last4",
            "card_holder_name",
            "expiry_month",
            "expiry_year",
            "is_active",
            "account_credit_limit",
            "created_at",
        ):
            self.assertIn(field, details)
        self.assertEqual(details["masked_card_number"], "************5555")
        self.assertFalse(details["is_active"])
        self.assertNotIn("cvv", details)
        self.assertNotIn("card_number", details)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="PaySecure <no-reply@example.com>",
    )
    def test_blocking_a_card_sends_a_blocked_card_email(self):
        mail.outbox.clear()
        self.user.email = "carduser@example.com"
        self.user.save(update_fields=["email"])
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        card = Card.objects.create(
            user=self.user,
            card_type="CREDIT",
            masked_card_number="************1111",
            last4="1111",
            card_holder_name="Test",
            expiry_month=12,
            expiry_year=2030,
        )
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(
                f"/api/admin/cards/{card.id}/",
                {"is_active": False},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("blocked", mail.outbox[0].subject.lower())
        self.assertIn("Your card **** 1111 has been blocked", mail.outbox[0].body)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="PaySecure <no-reply@example.com>",
    )
    def test_lowering_credit_limit_below_ten_percent_sends_threshold_alert(self):
        mail.outbox.clear()
        self.user.email = "carduser@example.com"
        self.user.save(update_fields=["email"])
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        card = Card.objects.create(
            user=self.user,
            card_type="CREDIT",
            masked_card_number="************1111",
            last4="1111",
            card_holder_name="Test",
            expiry_month=12,
            expiry_year=2030,
        )
        UserCreditProfile.objects.filter(user=self.user).update(
            credit_limit=Decimal("20000.00")
        )
        Transaction.objects.create(
            user=self.user,
            card=card,
            amount="15000.00",
            status=Transaction.Status.SUCCESS,
            reference="TX-LIMIT-LOW-CREDIT",
        )
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(
                f"/api/admin/cards/{card.id}/",
                {"credit_limit": "16000.00"},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue(
            any("below 10%" in message.subject.lower() for message in mail.outbox)
        )
        self.assertTrue(
            any("available credit is now 1000.00" in message.body for message in mail.outbox)
        )
