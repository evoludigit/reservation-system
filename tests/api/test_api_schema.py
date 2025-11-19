import pytest
from django.test import Client
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestAPISchema:
    def setup_method(self):
        self.client = Client()
        self.api_client = APIClient()

    def test_openapi_schema_available(self):
        """OpenAPI schema is accessible at /api/schema/"""
        url = "/api/schema/"
        response = self.api_client.get(url)

        assert response.status_code == 200
        assert "openapi" in response.data
        assert "paths" in response.data
        assert "/api/bookings/" in response.data["paths"]

    def test_swagger_ui_available(self):
        """Swagger UI documentation is accessible at /api/docs/"""
        url = "/api/docs/"
        response = self.client.get(url)

        assert response.status_code == 200
        # Check that it contains Swagger UI elements
        content = response.content.decode("utf-8")
        assert "swagger" in content.lower()

    def test_redoc_ui_available(self):
        """ReDoc UI documentation is accessible at /api/redoc/"""
        url = "/api/redoc/"
        response = self.client.get(url)

        assert response.status_code == 200
        # Check that it contains ReDoc elements
        content = response.content.decode("utf-8")
        assert "redoc" in content.lower()

    def test_schema_includes_booking_endpoints(self):
        """Schema includes all booking CRUD endpoints"""
        url = "/api/schema/"
        response = self.api_client.get(url)

        assert response.status_code == 200
        paths = response.data["paths"]

        # Check for all booking endpoints
        assert "/api/bookings/" in paths
        booking_paths = paths["/api/bookings/"]

        # Should have GET (list) and POST (create)
        assert "get" in booking_paths
        assert "post" in booking_paths

    def test_schema_includes_components(self):
        """Schema includes proper component definitions"""
        url = "/api/schema/"
        response = self.api_client.get(url)

        assert response.status_code == 200
        assert "components" in response.data
        components = response.data["components"]

        # Should have schemas for our models
        assert "schemas" in components
        schemas = components["schemas"]

        # Check for our main schemas
        assert "Booking" in schemas
        assert "BookingCreateRequest" in schemas
        assert "PaginatedBookingList" in schemas  # Pagination schema

        # Check that Booking schema has the expected fields
        booking_schema = schemas["Booking"]
        assert "properties" in booking_schema
        properties = booking_schema["properties"]

        # Check for key booking fields
        assert "id" in properties
        assert "accommodation_id" in properties
        assert "accommodation_name" in properties
        assert "booker_id" in properties
        assert "booker_name" in properties
        assert "start_date" in properties
        assert "end_date" in properties
        assert "number_of_guests" in properties
        assert "status" in properties
