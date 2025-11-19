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