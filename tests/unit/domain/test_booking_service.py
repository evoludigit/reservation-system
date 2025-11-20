# tests/unit/domain/test_booking_service.py
from datetime import date

import pytest

from bookings.domain.exceptions import BookingValidationError
from bookings.domain.services import BookingService
from bookings.domain.value_objects import DateRange
from bookings.infrastructure.repositories import (
    DjangoAccommodationRepository,
    DjangoBookerRepository,
    DjangoBookingRepository,
)
from bookings.models import Accommodation, Booker


class TestBookingService:
    def test_validate_date_range(self):
        """Service validates booking date range"""
        # Create service with mock repositories (not used in this test)
        booking_repo = DjangoBookingRepository()
        accommodation_repo = DjangoAccommodationRepository()
        booker_repo = DjangoBookerRepository()
        service = BookingService(booking_repo, accommodation_repo, booker_repo)

        date_range = DateRange(date(2026, 6, 1), date(2026, 6, 10))

        # Should not raise exception
        service.validate_date_range(date_range)

        # Past dates invalid
        past_range = DateRange(date(2024, 1, 1), date(2024, 1, 10))
        with pytest.raises(BookingValidationError):
            service.validate_date_range(past_range)

    @pytest.mark.django_db
    def test_create_booking_with_validation(self):
        """Service creates booking with full validation"""
        # Setup repositories
        booking_repo = DjangoBookingRepository()
        accommodation_repo = DjangoAccommodationRepository()
        booker_repo = DjangoBookerRepository()
        service = BookingService(booking_repo, accommodation_repo, booker_repo)

        # Create test data
        accommodation = Accommodation.objects.create(
            name="Test House", capacity=4, price_per_night=100
        )
        booker = Booker.objects.create(
            name="Test Booker", group_size=2, email="test@example.com", phone="1234567890"
        )

        date_range = DateRange(date(2026, 6, 1), date(2026, 6, 10))

        # Create booking through service
        booking = service.create_booking(
            accommodation_id=accommodation.id,
            booker_id=booker.id,
            date_range=date_range,
            number_of_guests=2,
        )

        assert booking.id is not None
        assert booking.status == "pending"
        assert booking.duration_nights() == 9

    @pytest.mark.django_db
    def test_create_booking_validates_capacity(self):
        """Service validates number of guests against capacity"""
        booking_repo = DjangoBookingRepository()
        accommodation_repo = DjangoAccommodationRepository()
        booker_repo = DjangoBookerRepository()
        service = BookingService(booking_repo, accommodation_repo, booker_repo)

        accommodation = Accommodation.objects.create(
            name="Test House", capacity=4, price_per_night=100
        )
        booker = Booker.objects.create(
            name="Test Booker", group_size=2, email="test@example.com", phone="1234567890"
        )

        date_range = DateRange(date(2026, 6, 1), date(2026, 6, 10))

        # Too many guests
        with pytest.raises(BookingValidationError) as exc_info:
            service.create_booking(
                accommodation_id=accommodation.id,
                booker_id=booker.id,
                date_range=date_range,
                number_of_guests=10,  # Exceeds capacity of 4
            )

        assert "exceeds capacity" in str(exc_info.value)

    @pytest.mark.django_db
    def test_create_booking_validates_entities_exist(self):
        """Service validates that accommodation and booker exist"""
        booking_repo = DjangoBookingRepository()
        accommodation_repo = DjangoAccommodationRepository()
        booker_repo = DjangoBookerRepository()
        service = BookingService(booking_repo, accommodation_repo, booker_repo)

        date_range = DateRange(date(2026, 6, 1), date(2026, 6, 10))

        # Non-existent accommodation
        with pytest.raises(BookingValidationError) as exc_info:
            service.create_booking(
                accommodation_id=999999,
                booker_id=999999,
                date_range=date_range,
                number_of_guests=2,
            )

        assert "not found" in str(exc_info.value).lower()
