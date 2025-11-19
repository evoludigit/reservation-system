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


class BookingService:
    """Domain service for booking operations"""

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