# tests/unit/infrastructure/test_repositories.py
import pytest

from bookings.infrastructure.repositories import (
    DjangoAccommodationRepository,
    DjangoBookerRepository,
    DjangoBookingRepository,
)
from bookings.models import Accommodation, Booker, Booking
from datetime import date


@pytest.mark.django_db
class TestDjangoBookerRepository:
    def test_get_by_id_returns_booker(self):
        """Repository can retrieve booker by ID"""
        booker = Booker.objects.create(
            name="John Doe", email="john@example.com", phone="1234567890", group_size=2
        )
        repo = DjangoBookerRepository()

        result = repo.get_by_id(booker.id)

        assert result is not None
        assert result.id == booker.id
        assert result.name == "John Doe"

    def test_get_by_id_returns_none_if_not_found(self):
        """Repository returns None when booker doesn't exist"""
        repo = DjangoBookerRepository()
        result = repo.get_by_id(999999)
        assert result is None

    def test_save_creates_new_booker(self):
        """Repository can save a new booker"""
        repo = DjangoBookerRepository()
        booker = Booker(
            name="Jane Smith", email="jane@example.com", phone="0987654321", group_size=4
        )

        saved_booker = repo.save(booker)

        assert saved_booker.id is not None
        assert Booker.objects.filter(id=saved_booker.id).exists()

    def test_find_by_email_returns_booker(self):
        """Repository can find booker by email"""
        Booker.objects.create(
            name="Test User", email="test@example.com", phone="1234567890", group_size=1
        )
        repo = DjangoBookerRepository()

        result = repo.find_by_email("test@example.com")

        assert result is not None
        assert result.email == "test@example.com"

    def test_find_by_email_returns_none_if_not_found(self):
        """Repository returns None when email doesn't exist"""
        repo = DjangoBookerRepository()
        result = repo.find_by_email("nonexistent@example.com")
        assert result is None

    def test_get_all_returns_all_bookers(self):
        """Repository can retrieve all bookers"""
        Booker.objects.create(
            name="User 1", email="user1@example.com", phone="1111111111", group_size=2
        )
        Booker.objects.create(
            name="User 2", email="user2@example.com", phone="2222222222", group_size=3
        )
        repo = DjangoBookerRepository()

        all_bookers = repo.get_all()

        assert len(all_bookers) == 2


@pytest.mark.django_db
class TestDjangoAccommodationRepository:
    def test_get_by_id_returns_accommodation(self):
        """Repository can retrieve accommodation by ID"""
        accommodation = Accommodation.objects.create(
            name="Beach House", capacity=6, price_per_night=150.00
        )
        repo = DjangoAccommodationRepository()

        result = repo.get_by_id(accommodation.id)

        assert result is not None
        assert result.id == accommodation.id
        assert result.name == "Beach House"

    def test_get_by_id_returns_none_if_not_found(self):
        """Repository returns None when accommodation doesn't exist"""
        repo = DjangoAccommodationRepository()
        result = repo.get_by_id(999999)
        assert result is None

    def test_get_by_id_returns_none_if_inactive(self):
        """Repository returns None when accommodation is inactive"""
        accommodation = Accommodation.objects.create(
            name="Inactive House", capacity=4, price_per_night=100.00, is_active=False
        )
        repo = DjangoAccommodationRepository()

        result = repo.get_by_id(accommodation.id)

        assert result is None

    def test_save_creates_new_accommodation(self):
        """Repository can save a new accommodation"""
        repo = DjangoAccommodationRepository()
        accommodation = Accommodation(
            name="Mountain Cabin", capacity=4, price_per_night=120.00
        )

        saved_accommodation = repo.save(accommodation)

        assert saved_accommodation.id is not None
        assert Accommodation.objects.filter(id=saved_accommodation.id).exists()

    def test_find_by_name_returns_accommodation(self):
        """Repository can find accommodation by name"""
        Accommodation.objects.create(name="Villa Paradise", capacity=8, price_per_night=250.00)
        repo = DjangoAccommodationRepository()

        result = repo.find_by_name("Villa Paradise")

        assert result is not None
        assert result.name == "Villa Paradise"

    def test_get_active_returns_only_active_accommodations(self):
        """Repository returns only active accommodations"""
        Accommodation.objects.create(
            name="Active House 1", capacity=4, price_per_night=100.00, is_active=True
        )
        Accommodation.objects.create(
            name="Active House 2", capacity=6, price_per_night=150.00, is_active=True
        )
        Accommodation.objects.create(
            name="Inactive House", capacity=2, price_per_night=50.00, is_active=False
        )
        repo = DjangoAccommodationRepository()

        active = repo.get_active()

        assert len(active) == 2
        assert all(acc.is_active for acc in active)


@pytest.mark.django_db
class TestDjangoBookingRepository:
    def test_get_by_id_returns_booking(self):
        """Repository can retrieve booking by ID"""
        booker = Booker.objects.create(
            name="Test Booker", email="test@example.com", phone="1234567890", group_size=2
        )
        accommodation = Accommodation.objects.create(
            name="Test House", capacity=4, price_per_night=100.00
        )
        booking = Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 10),
            number_of_guests=2,
        )
        repo = DjangoBookingRepository()

        result = repo.get_by_id(booking.id)

        assert result is not None
        assert result.id == booking.id

    def test_get_by_id_returns_none_if_not_found(self):
        """Repository returns None when booking doesn't exist"""
        repo = DjangoBookingRepository()
        result = repo.get_by_id(999999)
        assert result is None

    def test_save_creates_new_booking(self):
        """Repository can save a new booking"""
        booker = Booker.objects.create(
            name="Test Booker", email="test@example.com", phone="1234567890", group_size=2
        )
        accommodation = Accommodation.objects.create(
            name="Test House", capacity=4, price_per_night=100.00
        )
        repo = DjangoBookingRepository()

        booking = Booking(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 10),
            number_of_guests=2,
        )
        saved_booking = repo.save(booking)

        assert saved_booking.id is not None
        assert Booking.objects.filter(id=saved_booking.id).exists()

    def test_find_by_accommodation_and_dates_returns_overlapping_bookings(self):
        """Repository finds bookings that overlap with date range"""
        booker = Booker.objects.create(
            name="Test Booker", email="test@example.com", phone="1234567890", group_size=2
        )
        accommodation = Accommodation.objects.create(
            name="Test House", capacity=4, price_per_night=100.00
        )
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 10),
            number_of_guests=2,
            status="confirmed",
        )
        repo = DjangoBookingRepository()

        # Overlapping range
        overlapping = repo.find_by_accommodation_and_dates(
            accommodation, date(2026, 6, 5), date(2026, 6, 15)
        )

        assert len(overlapping) == 1

    def test_find_by_accommodation_and_dates_ignores_cancelled(self):
        """Repository ignores cancelled bookings when finding overlaps"""
        booker = Booker.objects.create(
            name="Test Booker", email="test@example.com", phone="1234567890", group_size=2
        )
        accommodation = Accommodation.objects.create(
            name="Test House", capacity=4, price_per_night=100.00
        )
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 10),
            number_of_guests=2,
            status="cancelled",
        )
        repo = DjangoBookingRepository()

        overlapping = repo.find_by_accommodation_and_dates(
            accommodation, date(2026, 6, 5), date(2026, 6, 15)
        )

        assert len(overlapping) == 0

    def test_get_active_bookings_for_accommodation(self):
        """Repository retrieves all active bookings for an accommodation"""
        booker = Booker.objects.create(
            name="Test Booker", email="test@example.com", phone="1234567890", group_size=2
        )
        accommodation = Accommodation.objects.create(
            name="Test House", capacity=4, price_per_night=100.00
        )
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 10),
            number_of_guests=2,
            status="pending",
        )
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 10),
            number_of_guests=2,
            status="confirmed",
        )
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 10),
            number_of_guests=2,
            status="cancelled",
        )
        repo = DjangoBookingRepository()

        active = repo.get_active_bookings_for_accommodation(accommodation)

        assert len(active) == 2
        assert all(b.status in ["pending", "confirmed"] for b in active)
