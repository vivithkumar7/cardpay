from django.conf import settings
from django.db import migrations


ROLE_PERMISSIONS = {
    "Admin": (
        ("cards", "card", "view_all_cards"),
        ("cards", "card", "manage_cards"),
        ("cards", "card", "block_cards"),
        ("transactions", "transaction", "view_all_transactions"),
        ("transactions", "transaction", "view_analytics"),
    ),
    "Support": (
        ("cards", "card", "view_all_cards"),
        ("cards", "card", "block_cards"),
        ("transactions", "transaction", "view_all_transactions"),
        ("transactions", "transaction", "view_analytics"),
    ),
    "Read-Only": (
        ("cards", "card", "view_all_cards"),
        ("transactions", "transaction", "view_all_transactions"),
        ("transactions", "transaction", "view_analytics"),
    ),
}
PERMISSION_NAMES = {
    ("cards", "card", "view_all_cards"): "Can view all cards",
    ("cards", "card", "manage_cards"): "Can manage cards",
    ("cards", "card", "block_cards"): "Can block and unblock cards",
    ("transactions", "transaction", "view_all_transactions"): (
        "Can view all transactions"
    ),
    ("transactions", "transaction", "view_analytics"): (
        "Can view transaction analytics"
    ),
}


def seed_roles(apps, schema_editor):
    database = schema_editor.connection.alias
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))

    permission_ids = {}
    for app_label, model, codename in {
        item for permissions in ROLE_PERMISSIONS.values() for item in permissions
    }:
        content_type, _ = ContentType.objects.using(database).get_or_create(
            app_label=app_label,
            model=model,
        )
        permission, _ = Permission.objects.using(database).get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": PERMISSION_NAMES[(app_label, model, codename)]},
        )
        permission_ids[(app_label, model, codename)] = permission.pk

    for role_name, permissions in ROLE_PERMISSIONS.items():
        role, _ = Group.objects.using(database).get_or_create(name=role_name)
        role.permissions.set(
            permission_ids[permission] for permission in permissions
        )

    admin_role = Group.objects.using(database).get(name="Admin")
    for user in User.objects.using(database).filter(is_staff=True).iterator():
        user.groups.add(admin_role)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("cards", "0003_card_rbac_permissions"),
        ("transactions", "0002_transaction_rbac_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_roles, migrations.RunPython.noop),
    ]
