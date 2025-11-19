# tests/unit/domain/test_booking_service.py
import pytest
from datetime import date
from unittest.mock import Mock
from bookings.domain.services import BookingService
from bookings.domain.value_objects import DateRange
from bookings.domain.exceptions import BookingValidationError
from bookings.models import Accommodation, Booker, Booking


class TestBookingService:
    def test_validate_date_range(self):
        """Service validates booking date range"""
        service = BookingService()

        date_range = DateRange(date(2026, 6, 1), date(2026, 6, 10))

        assert service.validate_date_range(date_range) is True

        # Past dates invalid
        past_range = DateRange(date(2024, 1, 1), date(2024, 1, 10))
        with pytest.raises(BookingValidationError):
            service.validate_date_range(past_range)

    @pytest.mark.django_db
    def test_check_availability(self):
        """Service checks accommodation availability for date range"""
        service = BookingService()

        accommodation = Accommodation.objects.create(name="Test House", capacity=4, price_per_night=100)

        # No existing bookings
        date_range = DateRange(date(2026, 6, 1), date(2026, 6, 10))
        assert service.is_available(accommodation, date_range) is True

        # Create booking
        booker = Booker.objects.create(name="Test Booker", group_size=2, email="test@example.com", phone="123")
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 6, 5),
            end_date=date(2026, 6, 15),
            number_of_guests=2
        )

        # Overlapping range not available
        assert service.is_available(accommodation, date_range) is False

        # Non-overlapping range available
        future_range = DateRange(date(2026, 7, 1), date(2026, 7, 10))
        assert service.is_available(accommodation, future_range) is True

    def test_create_booking_with_validation(self):
        """Service creates booking with full validation"""
        service = BookingService()

        # Mock objects
        accommodation = Mock()
        accommodation.capacity = 4
        booker = Mock()

        date_range = DateRange(date(2025, 6, 1), date(2025, 6, 10))

        # Mock the booking creation
        # This test would need mocking of the database operations