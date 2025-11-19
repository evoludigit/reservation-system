class BookerService:
    """Domain service for booker-related business logic"""

    @staticmethod
    def validate_contact_information(email: str, phone: str) -> bool:
        """Validate booker contact information"""
        # Domain validation logic
        # For now, basic checks
        if not email or '@' not in email:
            return False
        if not phone or len(phone) < 10:
            return False
        return True


class AccommodationService:
    """Domain service for accommodation-related business logic"""

    @staticmethod
    def validate_accommodation_data(name: str, capacity: int, price: float) -> bool:
        """Validate accommodation data"""
        if not name or len(name.strip()) == 0:
            return False
        if capacity < 1:
            return False
        if price <= 0:
            return False
        return True


from django.db import transaction
from django.utils import timezone
from ..models import Booking, Accommodation
from .value_objects import DateRange
from .exceptions import BookingValidationError


class BookingService:
    """Domain service for booking operations"""

    def validate_date_range(self, date_range: DateRange) -> bool:
        """Validate booking date range against business rules"""
        today = timezone.now().date()

        if date_range.start_date < today:
            raise BookingValidationError("Cannot book dates in the past")

        if date_range.duration_days() < 1:
            raise BookingValidationError("Booking must be at least 1 night")

        if date_range.duration_days() > 365:
            raise BookingValidationError("Booking cannot exceed 365 nights")

        return True

    def is_available(self, accommodation: Accommodation, date_range: DateRange) -> bool:
        """Check if accommodation is available for the date range"""
        overlapping = Booking.objects.filter(
            accommodation=accommodation,
            start_date__lt=date_range.end_date,
            end_date__gt=date_range.start_date,
            status__in=['pending', 'confirmed']
        ).exists()

        return not overlapping

    @transaction.atomic
    def create_booking(
        self,
        accommodation: Accommodation,
        booker,
        date_range: DateRange,
        number_of_guests: int
    ) -> Booking:
        """Create a new booking with full validation"""
        # Validate date range
        self.validate_date_range(date_range)

        # Check availability
        if not self.is_available(accommodation, date_range):
            raise BookingValidationError(
                f"Accommodation not available from {date_range.start_date} to {date_range.end_date}"
            )

        # Validate capacity
        if number_of_guests > accommodation.capacity:
            raise BookingValidationError(
                f"Number of guests ({number_of_guests}) exceeds capacity ({accommodation.capacity})"
            )

        # Create booking
        booking = Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date_range.start_date,
            end_date=date_range.end_date,
            number_of_guests=number_of_guests,
            status='pending'
        )

        return booking

    @staticmethod
    def calculate_total_price(booking) -> float:
        """Calculate total price for a booking"""
        nights = booking.duration_nights()
        return booking.accommodation.price_per_night * nights

    @staticmethod
    def can_confirm_booking(booking) -> bool:
        """Check if booking can be confirmed"""
        return booking.status == 'pending'

    @staticmethod
    def can_cancel_booking(booking) -> bool:
        """Check if booking can be cancelled"""
        return booking.status in ['pending', 'confirmed']