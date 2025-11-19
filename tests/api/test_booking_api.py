# tests/api/test_booking_api.py
import pytest
from datetime import date
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from bookings.models import Accommodation, Booker, Booking


@pytest.mark.django_db
class TestBookingCreateAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_create_booking_success(self):
        """POST /api/bookings/ creates a new booking"""
        accommodation = Accommodation.objects.create(name="Beach House", capacity=6, price_per_night=150.00)
        booker = Booker.objects.create(name="John Doe", group_size=4, email="john@example.com", phone="+33612345678")

        url = reverse('booking-list')
        data = {
            'accommodation_id': accommodation.id,
            'booker_id': booker.id,
            'start_date': '2026-06-01',
            'end_date': '2026-06-10',
            'number_of_guests': 2
        }

        response = self.client.post(url, data, format='json')

        assert response.status_code == 201
        assert response.data['accommodation_id'] == accommodation.id
        assert response.data['status'] == 'pending'
        assert 'id' in response.data

    def test_create_booking_overlapping_dates_fails(self):
        """Overlapping booking returns 409 Conflict"""
        accommodation = Accommodation.objects.create(name="Beach House", capacity=6, price_per_night=150.00)
        booker = Booker.objects.create(name="John Doe", group_size=4, email="john@example.com", phone="+33612345678")

        # Create first booking
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 10),
            number_of_guests=2
        )

        url = reverse('booking-list')
        data = {
            'accommodation_id': accommodation.id,
            'booker_id': booker.id,
            'start_date': '2026-06-05',
            'end_date': '2026-06-15',
            'number_of_guests': 2
        }

        response = self.client.post(url, data, format='json')

        assert response.status_code == 409
        assert 'not available' in response.data['error'].lower()

    def test_create_booking_validation_errors(self):
        """Invalid data returns 400 Bad Request"""
        accommodation = Accommodation.objects.create(name="Beach House", capacity=6, price_per_night=150.00)
        booker = Booker.objects.create(name="John Doe", group_size=4, email="john@example.com", phone="+33612345678")

        url = reverse('booking-list')
        data = {
            'accommodation_id': accommodation.id,
            'booker_id': booker.id,
            'start_date': '2026-06-10',
            'end_date': '2026-06-01',  # End before start
            'number_of_guests': 2
        }

        response = self.client.post(url, data, format='json')

        assert response.status_code == 400