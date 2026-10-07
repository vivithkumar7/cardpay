from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_credit_profiles_for_existing_users(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    UserCreditProfile = apps.get_model("accounts", "UserCreditProfile")
    database = schema_editor.connection.alias
    UserCreditProfile.objects.using(database).bulk_create(
        [
            UserCreditProfile(user_id=user_id)
            for user_id in User.objects.using(database).values_list("pk", flat=True)
        ],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserCreditProfile",
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
                (
                    "credit_limit",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=12,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="credit_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.RunPython(
            create_credit_profiles_for_existing_users,
            migrations.RunPython.noop,
        ),
    ]
