from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DateRange:
    """Value object representing an immutable date range"""

    start_date: date
    end_date: date

    def __post_init__(self):
        """Validate date range on creation"""
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")

    def overlaps(self, other: "DateRange") -> bool:
        """Check if this date range overlaps with another"""
        return self.start_date < other.end_date and other.start_date < self.end_date

    def contains_date(self, check_date: date) -> bool:
        """Check if a specific date falls within this range"""
        return self.start_date <= check_date < self.end_date

    def duration_days(self) -> int:
        """Calculate the number of days in the range"""
        return (self.end_date - self.start_date).days

    def duration_nights(self) -> int:
        """Calculate the number of nights (days - 1)"""
        return max(0, self.duration_days() - 1)

    def __lt__(self, other: "DateRange") -> bool:
        """Compare by start date"""
        return self.start_date < other.start_date

    def __eq__(self, other: object) -> bool:
        """Value equality based on start and end dates"""
        if not isinstance(other, DateRange):
            return NotImplemented
        return self.start_date == other.start_date and self.end_date == other.end_date

    def __hash__(self) -> int:
        """Hash based on start and end dates"""
        return hash((self.start_date, self.end_date))
