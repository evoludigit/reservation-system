# tests/api/test_booking_api.py
from datetime import date

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from bookings.models import Accommodation, Booker, Booking


@pytest.mark.django_db
class TestBookingCreateAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_create_booking_success(self):
        """POST /api/bookings/ creates a new booking"""
        accommodation = Accommodation.objects.create(
            name="Beach House", capacity=6, price_per_night=150.00
        )
        booker = Booker.objects.create(
            name="John Doe", group_size=4, email="john@example.com", phone="+33612345678"
        )

        url = reverse("booking-list")
        data = {
            "accommodation_id": accommodation.id,
            "booker_id": booker.id,
            "start_date": "2026-06-01",
            "end_date": "2026-06-10",
            "number_of_guests": 2,
        }

        response = self.client.post(url, data, format="json")

        assert response.status_code == 201
        assert response.data["accommodation_id"] == accommodation.id
        assert response.data["status"] == "pending"
        assert "id" in response.data

    def test_create_booking_overlapping_dates_fails(self):
        """Overlapping booking returns 409 Conflict"""
        accommodation = Accommodation.objects.create(
            name="Beach House", capacity=6, price_per_night=150.00
        )
        booker = Booker.objects.create(
            name="John Doe", group_size=4, email="john@example.com", phone="+33612345678"
        )

        # Create first booking
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 10),
            number_of_guests=2,
        )

        url = reverse("booking-list")
        data = {
            "accommodation_id": accommodation.id,
            "booker_id": booker.id,
            "start_date": "2026-06-05",
            "end_date": "2026-06-15",
            "number_of_guests": 2,
        }

        response = self.client.post(url, data, format="json")

        assert response.status_code == 409
        assert "not available" in response.data["error"].lower()

    def test_create_booking_validation_errors(self):
        """Invalid data returns 400 Bad Request"""
        accommodation = Accommodation.objects.create(
            name="Beach House", capacity=6, price_per_night=150.00
        )
        booker = Booker.objects.create(
            name="John Doe", group_size=4, email="john@example.com", phone="+33612345678"
        )

        url = reverse("booking-list")
        data = {
            "accommodation_id": accommodation.id,
            "booker_id": booker.id,
            "start_date": "2026-06-10",
            "end_date": "2026-06-01",  # End before start
            "number_of_guests": 2,
        }

        response = self.client.post(url, data, format="json")

        assert response.status_code == 400


@pytest.mark.django_db
class TestBookingListAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_list_bookings_empty(self):
        """GET /api/bookings/ returns empty list when no bookings"""
        url = reverse("booking-list")
        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["results"] == []
        assert response.data["count"] == 0

    def test_list_bookings_with_data(self):
        """GET /api/bookings/ returns bookings when they exist"""
        accommodation = Accommodation.objects.create(
            name="Beach House", capacity=6, price_per_night=150.00
        )
        booker = Booker.objects.create(
            name="John Doe", group_size=4, email="john@example.com", phone="+33612345678"
        )

        booking = Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 10),
            number_of_guests=2,
        )

        url = reverse("booking-list")
        response = self.client.get(url)

        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == booking.id
        assert response.data["results"][0]["accommodation_name"] == "Beach House"
        assert response.data["results"][0]["booker_name"] == "John Doe"
        assert response.data["results"][0]["duration_nights"] == 9

    def test_filter_bookings_by_accommodation(self):
        """Can filter bookings by accommodation ID"""
        acc1 = Accommodation.objects.create(name="Beach House", capacity=6, price_per_night=150.00)
        acc2 = Accommodation.objects.create(
            name="Mountain Cabin", capacity=4, price_per_night=120.00
        )
        booker = Booker.objects.create(
            name="John Doe", group_size=4, email="john@example.com", phone="+33612345678"
        )

        Booking.objects.create(
            accommodation=acc1,
            booker=booker,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 10),
            number_of_guests=2,
        )
        Booking.objects.create(
            accommodation=acc2,
            booker=booker,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 10),
            number_of_guests=2,
        )

        url = reverse("booking-list")
        response = self.client.get(url, {"accommodation_id": acc1.id})

        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["accommodation_id"] == acc1.id

    def test_filter_bookings_by_date_range(self):
        """Can filter bookings by date range"""
        accommodation = Accommodation.objects.create(
            name="Beach House", capacity=6, price_per_night=150.00
        )
        booker = Booker.objects.create(
            name="John Doe", group_size=4, email="john@example.com", phone="+33612345678"
        )

        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 10),
            number_of_guests=2,
        )
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 10),
            number_of_guests=2,
        )

        url = reverse("booking-list")
        response = self.client.get(
            url, {"start_date_gte": "2026-05-01", "end_date_lte": "2026-07-01"}
        )

        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["start_date"] == "2026-06-01"

    def test_filter_bookings_by_status(self):
        """Can filter bookings by status"""
        accommodation = Accommodation.objects.create(
            name="Beach House", capacity=6, price_per_night=150.00
        )
        booker = Booker.objects.create(
            name="John Doe", group_size=4, email="john@example.com", phone="+33612345678"
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

        url = reverse("booking-list")
        response = self.client.get(url, {"status": "confirmed"})

        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["status"] == "confirmed"

    def test_pagination_works(self):
        """Pagination works for large result sets"""
        accommodation = Accommodation.objects.create(
            name="Beach House", capacity=6, price_per_night=150.00
        )
        booker = Booker.objects.create(
            name="John Doe", group_size=4, email="john@example.com", phone="+33612345678"
        )

        # Create 25 bookings (more than page_size=20)
        for i in range(25):
            Booking.objects.create(
                accommodation=accommodation,
                booker=booker,
                start_date=date(2026, 6, i + 1),
                end_date=date(2026, 6, i + 2),
                number_of_guests=2,
            )

        url = reverse("booking-list")
        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["count"] == 25
        assert len(response.data["results"]) == 20  # Default page size
        assert response.data["next"] is not None  # Should have next page
        assert response.data["previous"] is None  # First page

        # Test second page
        response2 = self.client.get(response.data["next"])
        assert response2.status_code == 200
        assert len(response2.data["results"]) == 5  # Remaining 5 bookings
        assert response2.data["next"] is None  # No more pages
        assert response2.data["previous"] is not None  # Has previous page
