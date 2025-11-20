# tests/integration/test_booking_concurrency.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

import pytest
from django.db import IntegrityError

from bookings.domain.exceptions import BookingValidationError
from bookings.domain.services import BookingService
from bookings.domain.value_objects import DateRange
from bookings.infrastructure.repositories import (
    DjangoAccommodationRepository,
    DjangoBookerRepository,
    DjangoBookingRepository,
)
from bookings.models import Accommodation, Booker, Booking


@pytest.mark.django_db(transaction=True)
class TestBookingConcurrency:
    def test_concurrent_booking_creation_prevents_overlap(self):
        """Multiple threads trying to book same dates should only succeed once"""
        # Create test data
        booker = Booker.objects.create(
            name="Test Booker", email="test@example.com", phone="1234567890", group_size=4
        )
        accommodation = Accommodation.objects.create(
            name="Test House", capacity=4, price_per_night=100
        )

        date_range = DateRange(date(2026, 6, 1), date(2026, 6, 10))

        def attempt_booking():
            """Attempt to create a booking"""
            try:
                # Create fresh repository instances for each thread
                booking_repo = DjangoBookingRepository()
                accommodation_repo = DjangoAccommodationRepository()
                booker_repo = DjangoBookerRepository()

                service = BookingService(booking_repo, accommodation_repo, booker_repo)
                return service.create_booking(
                    accommodation_id=accommodation.id,
                    booker_id=booker.id,
                    date_range=date_range,
                    number_of_guests=2,
                )
            except (BookingValidationError, IntegrityError):
                return None

        # Attempt 10 concurrent bookings
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(attempt_booking) for _ in range(10)]
            results = [f.result() for f in as_completed(futures)]

        # Only one should succeed
        successful = [r for r in results if r is not None]
        assert len(successful) == 1, f"Expected 1 successful booking, got {len(successful)}"
        assert successful[0].accommodation_id == accommodation.id

    def test_concurrent_bookings_different_dates_succeed(self):
        """Concurrent bookings for different dates should all succeed"""
        booker = Booker.objects.create(
            name="Test Booker", email="test@example.com", phone="1234567890", group_size=4
        )
        accommodation = Accommodation.objects.create(
            name="Test House", capacity=4, price_per_night=100
        )

        # Different date ranges that don't overlap
        date_ranges = [
            DateRange(date(2026, 6, 1), date(2026, 6, 5)),
            DateRange(date(2026, 6, 10), date(2026, 6, 15)),
            DateRange(date(2026, 6, 20), date(2026, 6, 25)),
        ]

        def attempt_booking(idx):
            """Attempt to create a booking with a specific date range"""
            try:
                booking_repo = DjangoBookingRepository()
                accommodation_repo = DjangoAccommodationRepository()
                booker_repo = DjangoBookerRepository()

                service = BookingService(booking_repo, accommodation_repo, booker_repo)
                return service.create_booking(
                    accommodation_id=accommodation.id,
                    booker_id=booker.id,
                    date_range=date_ranges[idx],
                    number_of_guests=2,
                )
            except (BookingValidationError, IntegrityError):
                return None

        # Attempt 3 concurrent bookings with different dates
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(attempt_booking, i) for i in range(3)]
            results = [f.result() for f in as_completed(futures)]

        # All should succeed
        successful = [r for r in results if r is not None]
        assert len(successful) == 3, f"Expected 3 successful bookings, got {len(successful)}"

    def test_concurrent_bookings_different_accommodations_succeed(self):
        """Concurrent bookings for different accommodations with same dates should succeed"""
        booker = Booker.objects.create(
            name="Test Booker", email="test@example.com", phone="1234567890", group_size=4
        )
        accommodations = [
            Accommodation.objects.create(name=f"House {i}", capacity=4, price_per_night=100)
            for i in range(3)
        ]

        date_range = DateRange(date(2026, 6, 1), date(2026, 6, 10))

        def attempt_booking(accommodation_id):
            """Attempt to create a booking for a specific accommodation"""
            try:
                booking_repo = DjangoBookingRepository()
                accommodation_repo = DjangoAccommodationRepository()
                booker_repo = DjangoBookerRepository()

                service = BookingService(booking_repo, accommodation_repo, booker_repo)
                return service.create_booking(
                    accommodation_id=accommodation_id,
                    booker_id=booker.id,
                    date_range=date_range,
                    number_of_guests=2,
                )
            except (BookingValidationError, IntegrityError):
                return None

        # Attempt concurrent bookings for different accommodations
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(attempt_booking, acc.id) for acc in accommodations]
            results = [f.result() for f in as_completed(futures)]

        # All should succeed
        successful = [r for r in results if r is not None]
        assert len(successful) == 3, f"Expected 3 successful bookings, got {len(successful)}"


@pytest.mark.django_db
class TestExclusionConstraintEnforcement:
    def test_exclusion_constraint_prevents_direct_model_creation(self):
        """PostgreSQL exclusion constraint prevents overlapping bookings at DB level"""
        booker = Booker.objects.create(
            name="Test Booker", email="test@example.com", phone="1234567890", group_size=4
        )
        accommodation = Accommodation.objects.create(
            name="Test House", capacity=4, price_per_night=100
        )

        # Create first booking
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 10),
            number_of_guests=2,
            status="confirmed",
        )

        # Attempt to create overlapping booking directly via model
        # This should be caught by the PostgreSQL exclusion constraint
        with pytest.raises(IntegrityError) as exc_info:
            Booking.objects.create(
                accommodation=accommodation,
                booker=booker,
                start_date=date(2026, 6, 5),
                end_date=date(2026, 6, 15),
                number_of_guests=2,
                status="confirmed",
            )

        # Verify it's the exclusion constraint
        assert "bookings_no_overlap" in str(exc_info.value) or "exclude" in str(exc_info.value).lower()

    def test_exclusion_constraint_allows_cancelled_overlaps(self):
        """Cancelled bookings don't trigger exclusion constraint"""
        booker = Booker.objects.create(
            name="Test Booker", email="test@example.com", phone="1234567890", group_size=4
        )
        accommodation = Accommodation.objects.create(
            name="Test House", capacity=4, price_per_night=100
        )

        # Create cancelled booking
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 10),
            number_of_guests=2,
            status="cancelled",
        )

        # Should allow new booking in same date range since first is cancelled
        booking = Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 10),
            number_of_guests=2,
            status="pending",
        )

        assert booking.id is not None
