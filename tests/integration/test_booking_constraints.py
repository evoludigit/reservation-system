# tests/integration/test_booking_constraints.py
from datetime import date

import pytest
from django.db import IntegrityError

from bookings.models import Accommodation, Booker, Booking


@pytest.mark.django_db
class TestBookingOverlapConstraint:
    def test_cannot_create_overlapping_bookings(self):
        """Application-level validation prevents overlapping bookings"""
        booker = Booker.objects.create(
            name="Test Booker", group_size=4, email="test@example.com", phone="1234567890"
        )
        accommodation = Accommodation.objects.create(
            name="Test House", capacity=4, price_per_night=100
        )

        # Create first booking
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 10),
            number_of_guests=2,
        )

        # Attempt overlapping booking - should fail
        with pytest.raises(IntegrityError) as exc_info:
            Booking.objects.create(
                accommodation=accommodation,
                booker=booker,
                start_date=date(2025, 6, 5),
                end_date=date(2025, 6, 15),
                number_of_guests=2,
            )

        assert "overlapping" in str(exc_info.value).lower()

    def test_adjacent_bookings_allowed(self):
        """Adjacent bookings (no overlap) are allowed"""
        booker = Booker.objects.create(
            name="Test Booker", group_size=4, email="test@example.com", phone="1234567890"
        )
        accommodation = Accommodation.objects.create(
            name="Test House", capacity=4, price_per_night=100
        )

        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 10),
            number_of_guests=2,
        )

        # Same day checkout/checkin is allowed (end is exclusive)
        booking2 = Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2025, 6, 10),
            end_date=date(2025, 6, 20),
            number_of_guests=2,
        )

        assert booking2.id is not None

    def test_different_accommodations_can_overlap(self):
        """Same dates are allowed for different accommodations"""
        booker = Booker.objects.create(
            name="Test Booker", group_size=4, email="test@example.com", phone="1234567890"
        )
        acc1 = Accommodation.objects.create(name="House 1", capacity=4, price_per_night=100)
        acc2 = Accommodation.objects.create(name="House 2", capacity=4, price_per_night=100)

        Booking.objects.create(
            accommodation=acc1,
            booker=booker,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 10),
            number_of_guests=2,
        )

        booking2 = Booking.objects.create(
            accommodation=acc2,
            booker=booker,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 10),
            number_of_guests=2,
        )

        assert booking2.id is not None
