# tests/unit/domain/test_value_objects.py
import pytest
from datetime import date
from bookings.domain.value_objects import DateRange


class TestDateRangeValueObject:
    def test_create_valid_date_range(self):
        """DateRange can be created with valid start and end dates"""
        start = date(2025, 1, 1)
        end = date(2025, 1, 10)
        date_range = DateRange(start, end)
        assert date_range.start_date == start
        assert date_range.end_date == end

    def test_end_date_must_be_after_start_date(self):
        """DateRange validates end > start"""
        with pytest.raises(ValueError):
            DateRange(date(2025, 1, 10), date(2025, 1, 1))

    def test_date_range_overlap_detection(self):
        """Detect overlapping date ranges"""
        range1 = DateRange(date(2025, 1, 1), date(2025, 1, 10))
        range2 = DateRange(date(2025, 1, 5), date(2025, 1, 15))
        range3 = DateRange(date(2025, 1, 11), date(2025, 1, 20))

        assert range1.overlaps(range2) is True
        assert range1.overlaps(range3) is False

    def test_date_range_immutability(self):
        """DateRange is immutable (value object property)"""
        date_range = DateRange(date(2025, 1, 1), date(2025, 1, 10))
        with pytest.raises(AttributeError):
            date_range.start_date = date(2025, 1, 2)