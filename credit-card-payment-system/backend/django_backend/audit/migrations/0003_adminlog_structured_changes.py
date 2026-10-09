from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("audit", "0002_adminlog_table_name")]

    operations = [
        migrations.AddField(
            model_name="adminlog",
            name="target_type",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="adminlog",
            name="target_id",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="adminlog",
            name="changes",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
