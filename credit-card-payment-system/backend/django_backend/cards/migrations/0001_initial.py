from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(
        name="Card",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("card_type", models.CharField(choices=[("CREDIT","Credit"),("DEBIT","Debit")], max_length=10)),
            ("masked_card_number", models.CharField(max_length=19)),
            ("last4", models.CharField(max_length=4)),
            ("card_holder_name", models.CharField(max_length=100)),
            ("expiry_month", models.PositiveSmallIntegerField()),
            ("expiry_year", models.PositiveSmallIntegerField()),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cards", to=settings.AUTH_USER_MODEL)),
        ],
    )]
