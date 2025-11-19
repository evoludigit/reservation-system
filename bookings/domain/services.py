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