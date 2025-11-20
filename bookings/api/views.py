from django.db import IntegrityError
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from ..domain.exceptions import BookingValidationError
from ..domain.services import BookingService
from ..domain.value_objects import DateRange
from ..infrastructure.repositories import (
    DjangoAccommodationRepository,
    DjangoBookerRepository,
    DjangoBookingRepository,
)
from ..models import Booking
from .filters import BookingFilter
from .serializers import BookingCreateSerializer, BookingSerializer


class BookingPagination(PageNumberPagination):
    """Pagination for booking list"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


@extend_schema(
    tags=["Bookings"],
    description="API for managing housing reservation bookings",
    summary="Booking Management API",
)
class BookingViewSet(viewsets.ModelViewSet):
    """API endpoint for booking management"""

    queryset = Booking.objects.select_related("accommodation", "booker").order_by("-created_at")

    serializer_class = BookingSerializer
    filterset_class = BookingFilter
    pagination_class = BookingPagination
    ordering_fields = ["start_date", "created_at", "accommodation__name"]
    search_fields = ["booker__name", "accommodation__name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize repositories for dependency injection
        self.booking_repo = DjangoBookingRepository()
        self.accommodation_repo = DjangoAccommodationRepository()
        self.booker_repo = DjangoBookerRepository()

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        return BookingSerializer

    @extend_schema(
        summary="List all bookings",
        description="Retrieve a paginated list of all bookings with optional filtering and search.",
        parameters=[
            OpenApiParameter(
                name="accommodation_id",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter by accommodation ID",
            ),
            OpenApiParameter(
                name="start_date_gte",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter bookings starting on or after this date (YYYY-MM-DD)",
            ),
            OpenApiParameter(
                name="end_date_lte",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter bookings ending on or before this date (YYYY-MM-DD)",
            ),
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by booking status (pending, confirmed, cancelled)",
            ),
            OpenApiParameter(
                name="search",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search in booker names and accommodation names",
            ),
            OpenApiParameter(
                name="ordering",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Order by field (start_date, created_at, accommodation__name)",
            ),
        ],
        examples=[
            OpenApiExample(
                "List all bookings",
                value={"count": 2, "results": [{"id": 1, "accommodation_name": "Beach House"}]},
                response_only=True,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new booking",
        description="Create a new booking reservation with validation for availability and capacity.",
        request=BookingCreateSerializer,
        responses={
            201: BookingSerializer,
            400: {
                "description": "Validation Error",
                "content": {
                    "application/json": {"example": {"error": "End date must be after start date"}}
                },
            },
            409: {
                "description": "Conflict Error",
                "content": {
                    "application/json": {
                        "example": {"error": "Accommodation not available for selected dates"}
                    }
                },
            },
        },
        examples=[
            OpenApiExample(
                "Create booking request",
                value={
                    "accommodation_id": 1,
                    "booker_id": 1,
                    "start_date": "2026-06-01",
                    "end_date": "2026-06-10",
                    "number_of_guests": 2,
                },
                request_only=True,
            ),
            OpenApiExample(
                "Create booking response",
                value={
                    "id": 1,
                    "accommodation_id": 1,
                    "accommodation_name": "Beach House",
                    "booker_id": 1,
                    "booker_name": "John Doe",
                    "start_date": "2026-06-01",
                    "end_date": "2026-06-10",
                    "number_of_guests": 2,
                    "status": "pending",
                    "created_at": "2025-11-19T10:00:00Z",
                    "updated_at": "2025-11-19T10:00:00Z",
                },
                response_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        """Create a new booking with domain service"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Create service with repository dependencies
            service = BookingService(
                self.booking_repo, self.accommodation_repo, self.booker_repo
            )

            booking = service.create_booking(
                accommodation_id=serializer.validated_data["accommodation"].id,
                booker_id=serializer.validated_data["booker"].id,
                date_range=DateRange(
                    serializer.validated_data["start_date"], serializer.validated_data["end_date"]
                ),
                number_of_guests=serializer.validated_data["number_of_guests"],
            )

            output_serializer = BookingSerializer(booking)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except BookingValidationError as e:
            # Check if it's availability or other validation
            if "not available" in str(e).lower() or "not found" in str(e).lower():
                return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            # Catch database constraint violations
            if "bookings_no_overlap" in str(e):
                return Response(
                    {"error": "Accommodation not available for selected dates"},
                    status=status.HTTP_409_CONFLICT,
                )
            return Response(
                {"error": "Database constraint violation"},
                status=status.HTTP_400_BAD_REQUEST,
            )
