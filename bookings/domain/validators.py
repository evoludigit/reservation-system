from .value_objects import DateRange
from .exceptions import BookingValidationError
from django.utils import timezone


class DateRangeValidator:
    """Validator for date range business rules"""

    @staticmethod
    def validate_future_dates(date_range: DateRange) -> None:
        """Ensure booking dates are in the future"""
        today = timezone.now().date()
        if date_range.start_date < today:
            raise BookingValidationError("Cannot book dates in the past")

    @staticmethod
    def validate_duration(date_range: DateRange) -> None:
        """Ensure booking duration is within limits"""
        days = date_range.duration_days()
        if days < 1:
            raise BookingValidationError("Booking must be at least 1 night")
        if days > 365:
            raise BookingValidationError("Booking cannot exceed 365 nights")


class AvailabilitySpecification:
    """Specification pattern for accommodation availability"""

    def __init__(self, accommodation):
        self.accommodation = accommodation

    def is_satisfied_by(self, date_range: DateRange) -> bool:
        """Check if accommodation is available for the date range"""
        from ..models import Booking
        overlapping = Booking.objects.filter(
            accommodation=self.accommodation,
            start_date__lt=date_range.end_date,
            end_date__gt=date_range.start_date,
            status__in=['pending', 'confirmed']
        ).exists()
        return not overlapping