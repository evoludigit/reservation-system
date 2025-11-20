from django.db import IntegrityError, transaction
from django.utils import timezone

from .exceptions import BookingValidationError
from .value_objects import DateRange


class BookerService:
    """Domain service for booker-related business logic"""

    @staticmethod
    def validate_contact_information(email: str, phone: str) -> bool:
        """Validate booker contact information"""
        # Domain validation logic
        # For now, basic checks
        if not email or "@" not in email:
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


class BookingService:
    """Domain service for booking operations - decoupled from infrastructure"""

    def __init__(self, booking_repository, accommodation_repository, booker_repository):
        """Initialize service with repository dependencies"""
        self.booking_repo = booking_repository
        self.accommodation_repo = accommodation_repository
        self.booker_repo = booker_repository

    def validate_date_range(self, date_range: DateRange) -> None:
        """Validate booking date range against business rules"""
        today = timezone.now().date()

        if date_range.start_date < today:
            raise BookingValidationError("Cannot book dates in the past")

        if date_range.duration_days() < 1:
            raise BookingValidationError("Booking must be at least 1 night")

        if date_range.duration_days() > 365:
            raise BookingValidationError("Booking cannot exceed 365 nights")

    @transaction.atomic
    def create_booking(
        self,
        accommodation_id: int,
        booker_id: int,
        date_range: DateRange,
        number_of_guests: int,
    ):
        """Create a new booking with full validation"""
        # Load entities via repositories
        accommodation = self.accommodation_repo.get_by_id(accommodation_id)
        if not accommodation:
            raise BookingValidationError(f"Accommodation {accommodation_id} not found")

        booker = self.booker_repo.get_by_id(booker_id)
        if not booker:
            raise BookingValidationError(f"Booker {booker_id} not found")

        # Validate date range
        self.validate_date_range(date_range)

        # Validate capacity
        if number_of_guests > accommodation.capacity:
            raise BookingValidationError(
                f"Number of guests ({number_of_guests}) exceeds capacity ({accommodation.capacity})"
            )

        # Create booking - database exclusion constraint prevents overlaps
        try:
            # Import here to avoid circular dependency
            from ..models import Booking

            booking = Booking(
                accommodation=accommodation,
                booker=booker,
                start_date=date_range.start_date,
                end_date=date_range.end_date,
                number_of_guests=number_of_guests,
                status="pending",
            )
            return self.booking_repo.save(booking)
        except IntegrityError as e:
            # Check if it's the exclusion constraint
            if "bookings_no_overlap" in str(e):
                raise BookingValidationError(
                    f"Accommodation not available from {date_range.start_date} to {date_range.end_date}"
                )
            raise

    @staticmethod
    def calculate_total_price(booking) -> float:
        """Calculate total price for a booking"""
        nights = booking.duration_nights()
        return float(booking.accommodation.price_per_night) * nights
