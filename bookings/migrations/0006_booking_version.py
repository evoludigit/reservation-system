# Generated manually - Add version field for optimistic locking

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0005_add_exclusion_constraint"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="version",
            field=models.IntegerField(default=0),
        ),
    ]
