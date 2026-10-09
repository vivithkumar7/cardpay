from django.db import migrations


def assign_fraud_review_permission(apps, schema_editor):
    database = schema_editor.connection.alias
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    content_type, _ = ContentType.objects.using(database).get_or_create(
        app_label="transactions",
        model="fraudalert",
    )
    permission, _ = Permission.objects.using(database).get_or_create(
        content_type=content_type,
        codename="review_fraud_alerts",
        defaults={"name": "Can review fraud alerts"},
    )
    for role_name in ("Admin", "Support"):
        Group.objects.using(database).get(name=role_name).permissions.add(permission)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_seed_rbac_roles"),
        ("transactions", "0003_fraud_detection"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(
            assign_fraud_review_permission,
            migrations.RunPython.noop,
        ),
    ]
