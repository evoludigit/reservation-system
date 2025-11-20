# Generated manually - Add PostgreSQL exclusion constraint for overlap prevention

from django.contrib.postgres.operations import CreateExtension
from django.db import connection, migrations


def apply_exclusion_constraint(apps, schema_editor):
    """Apply exclusion constraint only for PostgreSQL"""
    if connection.vendor == "postgresql":
        schema_editor.execute(
            """
            ALTER TABLE bookings
            ADD CONSTRAINT bookings_no_overlap
            EXCLUDE USING gist (
                accommodation_id WITH =,
                daterange(start_date, end_date, '[)') WITH &&
            )
            WHERE (status IN ('pending', 'confirmed'));
            """
        )


def reverse_exclusion_constraint(apps, schema_editor):
    """Remove exclusion constraint only for PostgreSQL"""
    if connection.vendor == "postgresql":
        schema_editor.execute(
            """
            ALTER TABLE bookings
            DROP CONSTRAINT IF EXISTS bookings_no_overlap;
            """
        )


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0004_booking_bookings_accommo_32d1c3_idx_and_more"),
    ]

    operations = [
        # Enable btree_gist extension (PostgreSQL only - no-op on other databases)
        CreateExtension("btree_gist"),
        # Add exclusion constraint to prevent overlapping bookings (PostgreSQL only)
        migrations.RunPython(
            apply_exclusion_constraint,
            reverse_exclusion_constraint,
        ),
    ]
