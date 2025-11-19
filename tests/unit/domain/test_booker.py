# tests/unit/domain/test_booker.py
import pytest
from django.core.exceptions import ValidationError
from bookings.models import Booker


class TestBookerEntity:
    @pytest.mark.django_db
    def test_create_booker_with_valid_data(self):
        """Booker can be created with name and size"""
        booker = Booker.objects.create(
            name="John Doe",
            group_size=4,
            email="john@example.com",
            phone="+33612345678"
        )
        assert booker.name == "John Doe"
        assert booker.group_size == 4

    def test_booker_group_size_must_be_positive(self):
        """Group size must be at least 1"""
        with pytest.raises(ValidationError):
            booker = Booker(name="Test", group_size=0, email="test@example.com", phone="123")
            booker.full_clean()

    def test_booker_string_representation(self):
        """String representation includes name and group size"""
        booker = Booker(name="Jane Smith", group_size=2, email="jane@example.com", phone="456")
        assert str(booker) == "Jane Smith (2 persons)"