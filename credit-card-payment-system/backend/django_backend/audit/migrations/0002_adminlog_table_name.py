from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_initial")]

    operations = [
        migrations.AlterModelTable(
            name="adminlog",
            table="admin_logs",
        ),
    ]
