# tests/unit/domain/test_booking.py
import pytest
from datetime import date
from django.core.exceptions import ValidationError
from bookings.models import Booking, Booker, Accommodation


class TestBookingEntity:
    @pytest.mark.django_db
    def test_create_booking_with_valid_data(self):
        """Booking can be created with all required fields"""
        booker = Booker.objects.create(
            name="John Doe",
            group_size=4,
            email="john@example.com",
            phone="+33612345678"
        )
        accommodation = Accommodation.objects.create(
            name="Beach House",
            capacity=6,
            price_per_night=150.00
        )
        booking = Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 10),
            number_of_guests=4
        )
        assert booking.accommodation == accommodation
        assert booking.booker == booker
        assert booking.duration_nights() == 9

    @pytest.mark.django_db
    def test_booking_end_date_must_be_after_start_date(self):
        """Database check constraint enforces valid date range"""
        booker = Booker.objects.create(name="Test", group_size=2, email="test@example.com", phone="123")
        accommodation = Accommodation.objects.create(name="Test House", capacity=4, price_per_night=100)
        with pytest.raises(ValidationError):
            booking = Booking(
                accommodation=accommodation,
                booker=booker,
                start_date=date(2025, 6, 10),
                end_date=date(2025, 6, 1),
                number_of_guests=2
            )
            booking.full_clean()

    @pytest.mark.django_db
    def test_booking_guests_cannot_exceed_capacity(self):
        """Domain validation prevents overbooking capacity"""
        booker = Booker.objects.create(name="Test", group_size=6, email="test@example.com", phone="123")
        accommodation = Accommodation.objects.create(name="Test House", capacity=4, price_per_night=100)
        with pytest.raises(ValidationError):
            booking = Booking(
                accommodation=accommodation,
                booker=booker,
                start_date=date(2025, 6, 1),
                end_date=date(2025, 6, 10),
                number_of_guests=6
            )
            booking.full_clean()