from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("cards", "0002_card_is_active")]

    operations = [
        migrations.AlterModelOptions(
            name="card",
            options={
                "permissions": [
                    ("view_all_cards", "Can view all cards"),
                    ("manage_cards", "Can manage cards"),
                    ("block_cards", "Can block and unblock cards"),
                ],
            },
        ),
    ]
