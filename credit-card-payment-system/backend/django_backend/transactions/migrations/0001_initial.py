from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [("cards","0001_initial"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(
        name="Transaction",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
            ("currency", models.CharField(default="INR", max_length=3)),
            ("status", models.CharField(choices=[("PENDING","Pending"),("SUCCESS","Success"),("FAILED","Failed")], default="PENDING", max_length=10)),
            ("reference", models.CharField(max_length=40, unique=True)),
            ("failure_reason", models.CharField(blank=True, max_length=255)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("card", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transactions", to="cards.card")),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transactions", to=settings.AUTH_USER_MODEL)),
        ],
        options={"ordering":["-created_at"]},
    )]
