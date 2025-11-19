from django_filters import rest_framework as filters

from ..models import Booking


class BookingFilter(filters.FilterSet):
    """Filter set for booking queries"""

    accommodation_id = filters.NumberFilter(field_name="accommodation")
    start_date_gte = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    end_date_lte = filters.DateFilter(field_name="end_date", lookup_expr="lte")

    class Meta:
        model = Booking
        fields = ["accommodation_id", "start_date_gte", "end_date_lte", "status"]
