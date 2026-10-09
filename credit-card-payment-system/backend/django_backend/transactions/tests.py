from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core import mail
from django.db import DatabaseError
from django.utils import timezone
from accounts.models import UserCreditProfile
from audit.models import AdminLog
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
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["reference"], "TX-TEST-1")

    def test_transaction_search_sort_and_pagination_are_server_side(self):
        for amount in range(1, 24):
            Transaction.objects.create(
                user=self.user,
                card=self.card,
                amount=amount,
                status=Transaction.Status.SUCCESS,
                reference=f"TX-PAGE-{amount:02}",
            )

        first_page = self.client.get("/api/transactions/")
        self.assertEqual(first_page.data["count"], 23)
        self.assertEqual(len(first_page.data["results"]), 20)
        self.assertIsNotNone(first_page.data["next"])
        second_page = self.client.get("/api/transactions/?page=2")
        self.assertEqual(len(second_page.data["results"]), 3)
        self.assertIsNotNone(second_page.data["previous"])

        filtered = self.client.get(
            "/api/transactions/?card_search=****1111&min_amount=21&ordering=amount"
        )
        self.assertEqual(filtered.data["count"], 3)
        self.assertEqual(
            [row["amount"] for row in filtered.data["results"]],
            ["21.00", "22.00", "23.00"],
        )
        descending = self.client.get("/api/transactions/?ordering=-amount&page_size=2")
        self.assertEqual(
            [row["amount"] for row in descending.data["results"]],
            ["23.00", "22.00"],
        )

    def test_transaction_search_rejects_invalid_ranges_and_sort_fields(self):
        for url in (
            "/api/transactions/?min_amount=not-a-number",
            "/api/transactions/?ordering=card_number",
            "/api/transactions/?from_date=not-a-date",
            "/api/transactions/?from_date=2026-10-10&to_date=2026-10-09",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 400)

    def test_card_usage_analytics_aggregate_spending_and_utilization(self):
        UserCreditProfile.objects.update_or_create(
            user=self.user,
            defaults={"credit_limit": Decimal("200.00")},
        )
        Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount=Decimal("50.00"),
            category=Transaction.Category.FOOD,
            status=Transaction.Status.SUCCESS,
            reference="TX-ANALYTICS-FOOD",
        )
        Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount=Decimal("25.00"),
            category=Transaction.Category.SHOPPING,
            status=Transaction.Status.SUCCESS,
            reference="TX-ANALYTICS-SHOPPING",
        )
        Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount=Decimal("500.00"),
            category=Transaction.Category.FOOD,
            status=Transaction.Status.FAILED,
            reference="TX-ANALYTICS-FAILED",
        )

        response = self.client.get("/api/transactions/analytics/usage/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["credit_limit"], "200.00")
        self.assertEqual(response.data["credit_spending"], "75.00")
        self.assertEqual(response.data["credit_utilization_percentage"], "37.50")
        self.assertEqual(
            {row["category"]: row["spending"] for row in response.data["category_spending"]},
            {"FOOD": "50.00", "SHOPPING": "25.00"},
        )
        self.assertEqual(response.data["transaction_status_counts"]["SUCCESS"], 2)
        self.assertEqual(response.data["transaction_status_counts"]["FAILED"], 1)
        self.assertEqual(len(response.data["monthly_spending"]), 6)
        self.assertEqual(len(response.data["daily_activity"]), 7)

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
        Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount=100,
            reference="TX-DAILY-1",
            fraud_status=Transaction.FraudStatus.FLAGGED,
        )

        response = self.client.get("/api/admin/summary/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["daily"]["total_transactions"], 1)
        self.assertEqual(response.data["daily"]["pending"], 1)
        self.assertEqual(response.data["flagged_transactions"], 1)

    def test_system_health_is_role_gated_and_reports_process_and_database(self):
        forbidden = self.client.get("/api/admin/system-health/")
        self.assertEqual(forbidden.status_code, 403)

        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        response = self.client.get("/api/admin/system-health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "healthy")
        self.assertEqual(response.data["database"], "healthy")
        self.assertIn("api_requests", response.data)
        self.assertIn("average_response_time_ms", response.data)
        self.assertEqual(response.data["monitoring_scope"], "This application process")

    def test_system_health_reports_database_failure_and_logs_it(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.client.force_authenticate(user=self.user)

        with patch(
            "transactions.views.connection.cursor",
            side_effect=DatabaseError("database unavailable"),
        ), self.assertLogs("transactions.views", level="ERROR"):
            response = self.client.get("/api/admin/system-health/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["status"], "degraded")
        self.assertEqual(response.data["database"], "unavailable")

    def test_analytics_export_supports_csv_and_pdf_for_analytics_roles(self):
        Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount=Decimal("125.50"),
            category=Transaction.Category.FOOD,
            status=Transaction.Status.SUCCESS,
            reference="TX-EXPORT-ANALYTICS",
        )
        self.user.groups.add(Group.objects.get(name="Support"))

        csv_response = self.client.get("/api/admin/analytics/export/?file_format=csv")
        pdf_response = self.client.get("/api/admin/analytics/export/?file_format=pdf")
        invalid_response = self.client.get(
            "/api/admin/analytics/export/?file_format=xlsx"
        )

        self.assertEqual(
            csv_response.status_code,
            200,
            csv_response.content[:500],
        )
        self.assertEqual(csv_response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn(b"Total successful spending (INR)", csv_response.content)
        self.assertIn(b"Food & dining", csv_response.content)
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))
        self.assertEqual(invalid_response.status_code, 400)

    def test_support_and_read_only_roles_can_view_analytics_and_export(self):
        Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount=100,
            reference="TX-ROLE-REPORT",
        )

        for role_name in ("Support", "Read-Only"):
            with self.subTest(role=role_name):
                self.user.groups.clear()
                self.user.groups.add(Group.objects.get(name=role_name))
                summary = self.client.get("/api/admin/summary/")
                export = self.client.get("/api/admin/export/")

                self.assertEqual(summary.status_code, 200)
                self.assertEqual(summary.data["total_transactions"], 1)
                self.assertEqual(export.status_code, 200)
                self.assertIn(b"TX-ROLE-REPORT", export.content)
                self.assertIn(b"Fraud Status", export.content)

    def test_support_and_read_only_roles_cannot_initiate_payments(self):
        secret = "test-internal-secret-key-long-enough"
        with override_settings(DJANGO_INTERNAL_SECRET=secret):
            for role_name in ("Support", "Read-Only"):
                with self.subTest(role=role_name):
                    self.user.groups.clear()
                    self.user.groups.add(Group.objects.get(name=role_name))
                    response = self.client.post(
                        "/api/internal/transactions/create/",
                        {
                            "user_id": self.user.id,
                            "card_id": self.card.id,
                            "amount": "25.00",
                            "reference": f"TX-{role_name}",
                        },
                        format="json",
                        HTTP_X_INTERNAL_SECRET=secret,
                    )

                    self.assertEqual(response.status_code, 403)
                    self.assertFalse(
                        Transaction.objects.filter(
                            reference=f"TX-{role_name}"
                        ).exists()
                    )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="PaySecure <no-reply@example.com>",
    )
    def test_three_high_value_payments_in_ten_minutes_are_flagged_and_alerted(self):
        from transactions.models import FraudAlert

        self.user.email = "customer@example.com"
        self.user.save(update_fields=["email"])
        support = User.objects.create_user(
            username="fraud-support",
            email="support@example.com",
            password="StrongPass123!",
        )
        support.groups.add(Group.objects.get(name="Support"))
        mail.outbox.clear()
        secret = "test-internal-secret-key-long-enough"

        with override_settings(DJANGO_INTERNAL_SECRET=secret):
            with self.captureOnCommitCallbacks(execute=True):
                responses = [
                    self.client.post(
                        "/api/internal/transactions/create/",
                        {
                            "user_id": self.user.id,
                            "card_id": self.card.id,
                            "amount": "5000.00",
                            "reference": f"TX-FRAUD-HIGH-{index}",
                            "source_ip": "192.0.2.10",
                            "device_id": "device-a",
                        },
                        format="json",
                        HTTP_X_INTERNAL_SECRET=secret,
                    )
                    for index in range(1, 4)
                ]

        self.assertEqual([response.status_code for response in responses], [201] * 3)
        self.assertEqual(responses[0].data["fraud_status"], "CLEAR")
        self.assertEqual(responses[1].data["fraud_status"], "CLEAR")
        self.assertEqual(responses[2].data["fraud_status"], "FLAGGED")
        alert = FraudAlert.objects.get(transaction__reference="TX-FRAUD-HIGH-3")
        self.assertEqual(
            alert.rule_codes,
            ["repeated_high_value_transactions"],
        )
        self.assertEqual(alert.review_status, FraudAlert.ReviewStatus.OPEN)
        self.assertNotEqual(
            Transaction.objects.get(reference="TX-FRAUD-HIGH-3").location_fingerprint,
            "192.0.2.10",
        )
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            {message.to[0] for message in mail.outbox},
            {"customer@example.com", "support@example.com"},
        )

    def test_rapid_location_and_device_changes_are_flagged(self):
        from transactions.models import FraudAlert

        secret = "test-internal-secret-key-long-enough"
        with override_settings(DJANGO_INTERNAL_SECRET=secret):
            first = self.client.post(
                "/api/internal/transactions/create/",
                {
                    "user_id": self.user.id,
                    "card_id": self.card.id,
                    "amount": "50.00",
                    "reference": "TX-FRAUD-LOCATION-1",
                    "source_ip": "192.0.2.10",
                    "device_id": "device-a",
                },
                format="json",
                HTTP_X_INTERNAL_SECRET=secret,
            )
            second = self.client.post(
                "/api/internal/transactions/create/",
                {
                    "user_id": self.user.id,
                    "card_id": self.card.id,
                    "amount": "50.00",
                    "reference": "TX-FRAUD-LOCATION-2",
                    "source_ip": "198.51.100.20",
                    "device_id": "device-b",
                },
                format="json",
                HTTP_X_INTERNAL_SECRET=secret,
            )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(second.data["fraud_status"], "FLAGGED")
        alert = FraudAlert.objects.get(
            transaction__reference="TX-FRAUD-LOCATION-2"
        )
        self.assertEqual(
            set(alert.rule_codes),
            {"rapid_location_change", "rapid_device_change"},
        )

    def test_high_value_transactions_older_than_ten_minutes_do_not_trigger_rule(self):
        old_transaction = Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount="5000.00",
            reference="TX-FRAUD-HIGH-OLD",
        )
        Transaction.objects.filter(pk=old_transaction.pk).update(
            created_at=timezone.now() - timedelta(minutes=11)
        )
        secret = "test-internal-secret-key-long-enough"

        with override_settings(DJANGO_INTERNAL_SECRET=secret):
            responses = [
                self.client.post(
                    "/api/internal/transactions/create/",
                    {
                        "user_id": self.user.id,
                        "card_id": self.card.id,
                        "amount": "5000.00",
                        "reference": f"TX-FRAUD-HIGH-RECENT-{index}",
                    },
                    format="json",
                    HTTP_X_INTERNAL_SECRET=secret,
                )
                for index in range(1, 3)
            ]

        self.assertEqual([response.status_code for response in responses], [201] * 2)
        self.assertTrue(
            all(response.data["fraud_status"] == "CLEAR" for response in responses)
        )

    def test_support_can_review_fraud_alerts_read_only_can_only_view(self):
        from transactions.models import FraudAlert

        transaction = Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount="100.00",
            reference="TX-FRAUD-REVIEW",
            fraud_status=Transaction.FraudStatus.FLAGGED,
        )
        alert = FraudAlert.objects.create(
            transaction=transaction,
            user=self.user,
            rule_codes=["rapid_location_change"],
        )

        self.user.groups.add(Group.objects.get(name="Support"))
        listed = self.client.get("/api/admin/fraud-alerts/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data["results"][0]["reference"], "TX-FRAUD-REVIEW")
        reviewed = self.client.patch(
            f"/api/admin/fraud-alerts/{alert.id}/",
            {"review_status": "REVIEWED"},
            format="json",
        )
        self.assertEqual(reviewed.status_code, 200)
        alert.refresh_from_db()
        self.assertEqual(alert.reviewed_by, self.user)
        self.assertIsNotNone(alert.reviewed_at)
        audit_log = AdminLog.objects.get(
            admin_user=self.user,
            action="fraud_alert_reviewed",
            target_type="transaction",
            target_id=str(transaction.pk),
        )
        self.assertEqual(
            audit_log.changes["fraud_review_status"],
            {"before": "OPEN", "after": "REVIEWED"},
        )

        self.user.groups.clear()
        self.user.groups.add(Group.objects.get(name="Read-Only"))
        self.assertEqual(
            self.client.get("/api/admin/fraud-alerts/").status_code, 200
        )
        self.assertEqual(
            self.client.patch(
                f"/api/admin/fraud-alerts/{alert.id}/",
                {"review_status": "FALSE_POSITIVE"},
                format="json",
            ).status_code,
            403,
        )

    def test_django_transaction_admin_records_and_displays_changes(self):
        from django.contrib.admin.sites import site
        from django.test import RequestFactory
        from transactions.admin import TransactionAdmin

        transaction = Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount="100.00",
            reference="TX-ADMIN-AUDIT",
        )
        transaction.status = Transaction.Status.SUCCESS
        request = RequestFactory().post("/admin/transactions/transaction/")
        request.user = self.user
        transaction_admin = TransactionAdmin(Transaction, site)

        transaction_admin.save_model(request, transaction, form=None, change=True)

        log = AdminLog.objects.get(
            action="transaction_updated",
            target_type="transaction",
            target_id=str(transaction.pk),
        )
        self.assertEqual(
            log.changes["status"],
            {"before": Transaction.Status.PENDING, "after": Transaction.Status.SUCCESS},
        )
        self.assertIn(
            "transaction_updated",
            str(transaction_admin.audit_history(transaction)),
        )

    def test_admin_can_add_a_manual_audit_note(self):
        admin_user = User.objects.create_user(username="audit-admin")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save(update_fields=["is_staff", "is_superuser"])
        self.client.force_login(admin_user)

        add_page = self.client.get("/admin/audit/adminlog/add/")
        self.assertEqual(add_page.status_code, 200)
        response = self.client.post(
            "/admin/audit/adminlog/add/",
            {"details": "Documented an investigation outside the payment flow."},
        )

        self.assertEqual(response.status_code, 302)
        log = AdminLog.objects.get(action="manual_note")
        self.assertEqual(log.admin_user, admin_user)
        self.assertEqual(log.target_type, "admin_note")
        self.assertEqual(log.target_id, "")
        self.assertEqual(log.changes, {})
        self.assertEqual(
            log.details,
            "Documented an investigation outside the payment flow.",
        )

    def test_admin_can_add_fraud_alert_and_it_flags_transaction(self):
        from transactions.models import FraudAlert

        admin_user = User.objects.create_user(username="fraud-admin")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save(update_fields=["is_staff", "is_superuser"])
        self.client.force_login(admin_user)
        payment = Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount="125.00",
            reference="TX-MANUAL-FRAUD-ALERT",
        )

        add_page = self.client.get("/admin/transactions/fraudalert/add/")
        self.assertEqual(add_page.status_code, 200)
        response = self.client.post(
            "/admin/transactions/fraudalert/add/",
            {
                "transaction": str(payment.pk),
                "rule_codes": '["manual_review"]',
            },
        )

        self.assertEqual(response.status_code, 302)
        alert = FraudAlert.objects.get(transaction=payment)
        self.assertEqual(alert.user, self.user)
        self.assertEqual(alert.rule_codes, ["manual_review"])
        payment.refresh_from_db()
        self.assertEqual(payment.fraud_status, Transaction.FraudStatus.FLAGGED)
        self.assertTrue(
            AdminLog.objects.filter(
                admin_user=admin_user,
                action="fraud_alert_manually_created",
                target_type="fraud_alert",
                target_id=str(alert.pk),
            ).exists()
        )

    def test_admin_role_has_admin_add_permissions_and_read_only_does_not(self):
        from django.contrib.auth.models import Group

        admin_user = User.objects.create_user(username="role-admin")
        admin_user.is_staff = True
        admin_user.save(update_fields=["is_staff"])
        admin_user.groups.add(Group.objects.get(name="Admin"))
        self.client.force_login(admin_user)

        self.assertEqual(
            self.client.get("/admin/audit/adminlog/add/").status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/admin/transactions/fraudalert/add/").status_code,
            200,
        )

        admin_user.groups.clear()
        admin_user.groups.add(Group.objects.get(name="Read-Only"))
        self.client.logout()
        self.client.force_login(admin_user)
        self.assertEqual(
            self.client.get("/admin/audit/adminlog/add/").status_code,
            403,
        )
        self.assertEqual(
            self.client.get("/admin/transactions/fraudalert/add/").status_code,
            403,
        )

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

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="PaySecure <no-reply@example.com>",
        DJANGO_INTERNAL_SECRET="test-internal-secret-key-long-enough",
    )
    def test_finalized_transaction_sends_a_payment_status_email(self):
        self.user.email = "txuser@example.com"
        self.user.save(update_fields=["email"])
        transaction = Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount="12.50",
            reference="TX-EMAIL-RESULT",
        )
        secret = "test-internal-secret-key-long-enough"
        mail.outbox.clear()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(
                f"/api/internal/transactions/{transaction.reference}/",
                {"status": Transaction.Status.SUCCESS},
                format="json",
                HTTP_X_INTERNAL_SECRET=secret,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(transaction.reference, mail.outbox[0].body)
        self.assertIn("1111", mail.outbox[0].body)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="PaySecure <no-reply@example.com>",
        DJANGO_INTERNAL_SECRET="test-internal-secret-key-long-enough",
    )
    def test_finalized_payment_over_5000_sends_high_value_alert_even_if_failed(self):
        self.user.email = "txuser@example.com"
        self.user.save(update_fields=["email"])
        transaction = Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount="5000.01",
            reference="TX-HIGH-FAILED",
        )
        mail.outbox.clear()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(
                f"/api/internal/transactions/{transaction.reference}/",
                {
                    "status": Transaction.Status.FAILED,
                    "failure_reason": "Simulated failure.",
                },
                format="json",
                HTTP_X_INTERNAL_SECRET="test-internal-secret-key-long-enough",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("high-value", mail.outbox[0].subject.lower())
        self.assertIn("₹5,000", mail.outbox[0].body)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="PaySecure <no-reply@example.com>",
        DJANGO_INTERNAL_SECRET="test-internal-secret-key-long-enough",
    )
    def test_successful_credit_payment_that_crosses_below_ten_percent_alerts(self):
        self.user.email = "txuser@example.com"
        self.user.save(update_fields=["email"])
        UserCreditProfile.objects.filter(user=self.user).update(
            credit_limit=Decimal("10000.00")
        )
        transaction = Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount="9100.00",
            reference="TX-LOW-CREDIT",
        )
        mail.outbox.clear()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(
                f"/api/internal/transactions/{transaction.reference}/",
                {"status": Transaction.Status.SUCCESS},
                format="json",
                HTTP_X_INTERNAL_SECRET="test-internal-secret-key-long-enough",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)
        subjects = [message.subject.lower() for message in mail.outbox]
        self.assertTrue(any("below 10%" in subject for subject in subjects))
        self.assertTrue(any("high-value" in subject for subject in subjects))
        self.assertTrue(
            any("available credit is now 900.00" in message.body for message in mail.outbox)
        )

    def test_monthly_statement_pdf_is_authenticated_and_uses_valid_months(self):
        current_month = timezone.localdate().strftime("%Y-%m")
        self.client.credentials()
        response = self.client.get(
            f"/api/transactions/statement/?month={current_month}"
        )
        self.assertEqual(response.status_code, 401)

        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(
            f"/api/transactions/statement/?month={current_month}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(f"paysecure-statement-{current_month}.pdf", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_statement_rejects_invalid_and_future_months(self):
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        for month in ("2026-13", "202610", "not-a-month"):
            with self.subTest(month=month):
                response = self.client.get(
                    f"/api/transactions/statement/?month={month}"
                )
                self.assertEqual(response.status_code, 400)

        future_month = (
            f"{timezone.localdate().year + 1:04d}-01"
        )
        response = self.client.get(
            f"/api/transactions/statement/?month={future_month}"
        )
        self.assertEqual(response.status_code, 400)

    def test_statement_contains_month_rows_and_only_the_signed_in_users_data(self):
        own_transaction = Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount="25.00",
            status=Transaction.Status.SUCCESS,
            reference="TX-STATEMENT-OWN",
        )
        failed_transaction = Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount="10.00",
            status=Transaction.Status.FAILED,
            reference="TX-STATEMENT-FAILED",
        )
        pending_transaction = Transaction.objects.create(
            user=self.user,
            card=self.card,
            amount="5.00",
            status=Transaction.Status.PENDING,
            reference="TX-STATEMENT-PENDING",
        )
        other_user = User.objects.create_user(
            username="statement-other",
            password="StrongPass123!",
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
            amount="99.00",
            status=Transaction.Status.SUCCESS,
            reference="TX-STATEMENT-OTHER",
        )
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        month = own_transaction.created_at.astimezone(
            timezone.get_current_timezone()
        ).strftime("%Y-%m")

        with patch(
            "transactions.statements.MonthlyStatementPdfView._render_statement",
            return_value=b"%PDF test statement",
        ) as render_statement:
            response = self.client.get(
                f"/api/transactions/statement/?month={month}"
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))
        username, statement_month, rows, total_spent = render_statement.call_args.args
        self.assertEqual(username, self.user.get_username())
        self.assertEqual(statement_month, month)
        self.assertEqual(
            {row.reference for row in rows},
            {
                "TX-STATEMENT-OWN",
                "TX-STATEMENT-FAILED",
                "TX-STATEMENT-PENDING",
            },
        )
        self.assertEqual(total_spent, Decimal("25.00"))

    def test_statement_card_details_are_always_masked(self):
        from transactions.statements import _masked_card_details

        self.card.masked_card_number = "4111111111111111"
        self.card.last4 = "1111"

        card_details = _masked_card_details(self.card)

        self.assertIn("**** **** **** 1111", card_details)
        self.assertNotIn("4111111111111111", card_details)
