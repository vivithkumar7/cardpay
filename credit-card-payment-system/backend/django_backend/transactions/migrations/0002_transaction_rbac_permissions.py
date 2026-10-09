from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("transactions", "0001_initial")]

    operations = [
        migrations.AlterModelOptions(
            name="transaction",
            options={
                "ordering": ["-created_at"],
                "permissions": [
                    ("view_all_transactions", "Can view all transactions"),
                    ("view_analytics", "Can view transaction analytics"),
                ],
            },
        ),
    ]
