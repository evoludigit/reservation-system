from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import IntegrityError
from ..domain.services import BookingService
from ..domain.value_objects import DateRange
from ..domain.exceptions import BookingValidationError
from .serializers import BookingSerializer, BookingCreateSerializer
from ..models import Booking


class BookingViewSet(viewsets.ModelViewSet):
    """API endpoint for booking management"""

    queryset = Booking.objects.select_related(
        'accommodation', 'booker'
    ).order_by('-created_at')

    serializer_class = BookingSerializer
    filterset_fields = ['accommodation', 'booker', 'status']
    ordering_fields = ['start_date', 'created_at', 'accommodation__name']

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer

    def create(self, request, *args, **kwargs):
        """Create a new booking with domain service"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            service = BookingService()
            booking = service.create_booking(
                accommodation=serializer.validated_data['accommodation'],
                booker=serializer.validated_data['booker'],
                date_range=DateRange(
                    serializer.validated_data['start_date'],
                    serializer.validated_data['end_date']
                ),
                number_of_guests=serializer.validated_data['number_of_guests']
            )

            output_serializer = BookingSerializer(booking)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except BookingValidationError as e:
            # Check if it's availability or other validation
            if 'not available' in str(e).lower():
                return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
            else:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response(
                {'error': 'Accommodation not available for selected dates'},
                status=status.HTTP_409_CONFLICT
            )