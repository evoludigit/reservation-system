# tests/unit/domain/test_accommodation.py
import pytest
from django.core.exceptions import ValidationError

from bookings.models import Accommodation


class TestAccommodationEntity:
    @pytest.mark.django_db
    def test_create_accommodation_with_valid_data(self):
        """Accommodation can be created with name and capacity"""
        accommodation = Accommodation.objects.create(
            name="Beach House",
            capacity=6,
            description="Beautiful seaside property",
            price_per_night=150.00,
        )
        assert accommodation.name == "Beach House"
        assert accommodation.capacity == 6

    def test_accommodation_capacity_must_be_positive(self):
        """Capacity must be at least 1"""
        with pytest.raises(ValidationError):
            accommodation = Accommodation(name="Test", capacity=0, price_per_night=100)
            accommodation.full_clean()

    def test_accommodation_can_accommodate_group(self):
        """Domain method checks if group fits capacity"""
        accommodation = Accommodation(capacity=4, price_per_night=100)
        assert accommodation.can_accommodate(3) is True
        assert accommodation.can_accommodate(5) is False
