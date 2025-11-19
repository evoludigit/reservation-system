from rest_framework import serializers
from ..models import Booking, Accommodation, Booker


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for booking responses"""

    # Include accommodation details
    accommodation_name = serializers.CharField(source='accommodation.name', read_only=True)
    accommodation_capacity = serializers.IntegerField(source='accommodation.capacity', read_only=True)

    # Include booker details
    booker_name = serializers.CharField(source='booker.name', read_only=True)

    # Calculated fields
    duration_nights = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'accommodation_id',
            'accommodation_name',
            'accommodation_capacity',
            'booker_id',
            'booker_name',
            'start_date',
            'end_date',
            'duration_nights',
            'number_of_guests',
            'status',
            'created_at',
            'updated_at'
        ]

    def get_duration_nights(self, obj):
        return obj.duration_nights()


class BookingCreateSerializer(serializers.Serializer):
    """Serializer for booking creation requests"""

    accommodation_id = serializers.PrimaryKeyRelatedField(
        queryset=Accommodation.objects.filter(is_active=True),
        source='accommodation'
    )
    booker_id = serializers.PrimaryKeyRelatedField(
        queryset=Booker.objects.all(),
        source='booker'
    )
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    number_of_guests = serializers.IntegerField(min_value=1)