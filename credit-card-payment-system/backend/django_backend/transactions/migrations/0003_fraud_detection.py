from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("transactions", "0002_transaction_rbac_permissions"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="fraud_status",
            field=models.CharField(
                choices=[("CLEAR", "Clear"), ("FLAGGED", "Flagged")],
                default="CLEAR",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="location_fingerprint",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="transaction",
            name="device_fingerprint",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(
                fields=["user", "created_at"],
                name="tx_user_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(
                fields=["fraud_status", "created_at"],
                name="tx_fraud_created_idx",
            ),
        ),
        migrations.CreateModel(
            name="FraudAlert",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("rule_codes", models.JSONField(default=list)),
                (
                    "review_status",
                    models.CharField(
                        choices=[
                            ("OPEN", "Open"),
                            ("REVIEWED", "Reviewed"),
                            ("FALSE_POSITIVE", "False positive"),
                        ],
                        default="OPEN",
                        max_length=20,
                    ),
                ),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("detected_at", models.DateTimeField(auto_now_add=True)),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_fraud_alerts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "transaction",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fraud_alert",
                        to="transactions.transaction",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="fraud_alerts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-detected_at"],
                "permissions": [
                    ("review_fraud_alerts", "Can review fraud alerts"),
                ],
            },
        ),
        migrations.AddIndex(
            model_name="fraudalert",
            index=models.Index(
                fields=["review_status", "detected_at"],
                name="fraud_review_detected_idx",
            ),
        ),
    ]
