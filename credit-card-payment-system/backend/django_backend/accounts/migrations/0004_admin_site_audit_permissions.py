from django.db import migrations


ADMIN_SITE_PERMISSIONS = (
    ("audit", "adminlog", "view_adminlog", "Can view admin log"),
    ("audit", "adminlog", "add_adminlog", "Can add admin log"),
    ("transactions", "fraudalert", "view_fraudalert", "Can view fraud alert"),
    ("transactions", "fraudalert", "add_fraudalert", "Can add fraud alert"),
)
VIEW_FRAUD_PERMISSION = (
    "transactions",
    "fraudalert",
    "view_fraudalert",
)


def assign_admin_site_permissions(apps, schema_editor):
    database = schema_editor.connection.alias
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    permissions = {}
    for app_label, model_name, codename, name in ADMIN_SITE_PERMISSIONS:
        content_type, _ = ContentType.objects.using(database).get_or_create(
            app_label=app_label,
            model=model_name,
        )
        permission, _ = Permission.objects.using(database).get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": name},
        )
        permissions[(app_label, model_name, codename)] = permission

    admin_role = Group.objects.using(database).get(name="Admin")
    admin_role.permissions.add(
        *(
            permissions[(app_label, model_name, codename)]
            for app_label, model_name, codename, _ in ADMIN_SITE_PERMISSIONS
        )
    )

    fraud_view_permission = permissions[VIEW_FRAUD_PERMISSION]
    for role_name in ("Support", "Read-Only"):
        Group.objects.using(database).get(name=role_name).permissions.add(
            fraud_view_permission
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_assign_fraud_review_permission"),
        ("audit", "0003_adminlog_structured_changes"),
        ("transactions", "0004_remove_transaction_tx_user_created_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(
            assign_admin_site_permissions,
            migrations.RunPython.noop,
        ),
    ]
