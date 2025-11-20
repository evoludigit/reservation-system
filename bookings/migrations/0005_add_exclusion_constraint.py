# Generated manually - Add PostgreSQL exclusion constraint for overlap prevention

from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0004_booking_bookings_accommo_32d1c3_idx_and_more"),
    ]

    operations = [
        # Enable btree_gist extension for exclusion constraints
        CreateExtension("btree_gist"),
        # Add exclusion constraint to prevent overlapping bookings
        migrations.RunSQL(
            sql="""
                ALTER TABLE bookings
                ADD CONSTRAINT bookings_no_overlap
                EXCLUDE USING gist (
                    accommodation_id WITH =,
                    daterange(start_date, end_date, '[)') WITH &&
                )
                WHERE (status IN ('pending', 'confirmed'));
            """,
            reverse_sql="""
                ALTER TABLE bookings
                DROP CONSTRAINT IF EXISTS bookings_no_overlap;
            """,
        ),
    ]
