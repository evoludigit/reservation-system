# Housing Reservation System - COMPLEX

**Complexity**: Complex | **Phased TDD Approach**

## Executive Summary

Building a housing reservation management system using Django, PostgreSQL, Domain-Driven Design (DDD), and Test-Driven Development (TDD). The system ensures data integrity through PostgreSQL constraints and exclusion indexes to prevent overlapping bookings. Core domain entities include Booker (group of persons), Accommodation (housing), and Booking (reservation with date ranges).

## Architecture Principles

### Domain-Driven Design (DDD)
- **Entities**: Booker, Accommodation, Booking (with identity)
- **Value Objects**: DateRange (start_date, end_date)
- **Aggregates**: Booking aggregate root manages reservation consistency
- **Domain Services**: BookingValidator, AvailabilityChecker
- **Repository Pattern**: Abstract data access layer

### PostgreSQL Constraints Strategy
- **Exclusion Constraint**: Prevent overlapping bookings using `btree_gist` extension
- **Check Constraints**: Validate date ranges (end_date > start_date)
- **Unique Constraints**: Business rules enforcement
- **Foreign Key Constraints**: Referential integrity

### TDD Testing Layers
1. **Unit Tests**: Domain model logic and validation
2. **Integration Tests**: Database constraint enforcement
3. **API Tests**: Endpoint behavior and error handling

## PHASES

---

### Phase 0: Project Setup & Infrastructure

**Objective**: Initialize Django project with PostgreSQL, configure testing infrastructure, and enable required extensions.

#### TDD Cycle:

**1. RED**: Write failing infrastructure tests
- Test file: `tests/test_infrastructure.py`
- Expected failures:
  - Database connection fails
  - PostgreSQL version < 12
  - `btree_gist` extension not available
  - Django project structure missing

```python
# tests/test_infrastructure.py
def test_postgresql_connection():
    """Verify PostgreSQL database is accessible"""
    assert connection.vendor == 'postgresql'

def test_btree_gist_extension_enabled():
    """Verify btree_gist extension for exclusion constraints"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'btree_gist'")
        assert cursor.fetchone() is not None
```

**2. GREEN**: Minimal implementation
- Create Django project: `django-admin startproject reservation_system`
- Create app: `python manage.py startapp bookings`
- Configure `settings.py`:
  - PostgreSQL database configuration
  - Test database settings
  - Installed apps: `bookings`
- Create migration to enable `btree_gist` extension
- Install dependencies: `Django>=4.2`, `psycopg2-binary`, `pytest-django`

**3. REFACTOR**: Organize project structure
```
reservation_system/
├── bookings/
│   ├── domain/          # DDD domain layer
│   ├── infrastructure/  # Data access, repositories
│   ├── application/     # Use cases, services
│   └── api/            # REST API views
├── tests/
│   ├── unit/
│   ├── integration/
│   └── api/
└── manage.py
```

**4. QA**: Verify phase completion
- [ ] `pytest` runs successfully
- [ ] PostgreSQL connection established
- [ ] `btree_gist` extension enabled
- [ ] Project structure follows DDD layers

---

### Phase 1: Booker Domain Model

**Objective**: Implement Booker entity representing a group of persons with validation.

#### TDD Cycle:

**1. RED**: Write failing tests for Booker entity
- Test file: `tests/unit/domain/test_booker.py`
- Expected failures:
  - Booker model doesn't exist
  - Required fields validation fails
  - String representation incorrect

```python
# tests/unit/domain/test_booker.py
class TestBookerEntity:
    def test_create_booker_with_valid_data(self):
        """Booker can be created with name and size"""
        booker = Booker.objects.create(
            name="John Doe",
            group_size=4,
            email="john@example.com",
            phone="+33612345678"
        )
        assert booker.name == "John Doe"
        assert booker.group_size == 4

    def test_booker_group_size_must_be_positive(self):
        """Group size must be at least 1"""
        with pytest.raises(ValidationError):
            booker = Booker(name="Test", group_size=0)
            booker.full_clean()

    def test_booker_string_representation(self):
        """String representation includes name and group size"""
        booker = Booker(name="Jane Smith", group_size=2)
        assert str(booker) == "Jane Smith (2 persons)"
```

**2. GREEN**: Implement Booker model
- File: `bookings/domain/models.py`
- Minimal implementation:

```python
from django.db import models
from django.core.validators import MinValueValidator

class Booker(models.Model):
    """Domain entity representing a group booking a reservation"""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    group_size = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookers'

    def __str__(self):
        return f"{self.name} ({self.group_size} persons)"
```

**3. REFACTOR**: Add domain logic and value objects
- Extract email validation to domain service
- Add `BookerRepository` interface
- Implement repository pattern in `infrastructure/repositories.py`
- Add factory methods for common booker types

```python
# bookings/domain/services.py
class BookerService:
    """Domain service for booker-related business logic"""

    @staticmethod
    def validate_contact_information(email: str, phone: str) -> bool:
        """Validate booker contact information"""
        # Domain validation logic
        pass
```

**4. QA**: Verify phase completion
- [ ] All Booker tests pass
- [ ] Database migration created and applied
- [ ] Code follows DDD entity pattern
- [ ] Repository pattern implemented
- [ ] Validators enforce business rules

---

### Phase 2: Accommodation Domain Model

**Objective**: Implement Accommodation entity with capacity and availability rules.

#### TDD Cycle:

**1. RED**: Write failing tests for Accommodation entity
- Test file: `tests/unit/domain/test_accommodation.py`
- Expected failures:
  - Accommodation model doesn't exist
  - Capacity validation missing
  - Business rules not enforced

```python
# tests/unit/domain/test_accommodation.py
class TestAccommodationEntity:
    def test_create_accommodation_with_valid_data(self):
        """Accommodation can be created with name and capacity"""
        accommodation = Accommodation.objects.create(
            name="Beach House",
            capacity=6,
            description="Beautiful seaside property",
            price_per_night=150.00
        )
        assert accommodation.name == "Beach House"
        assert accommodation.capacity == 6

    def test_accommodation_capacity_must_be_positive(self):
        """Capacity must be at least 1"""
        with pytest.raises(ValidationError):
            accommodation = Accommodation(name="Test", capacity=0)
            accommodation.full_clean()

    def test_accommodation_can_accommodate_group(self):
        """Domain method checks if group fits capacity"""
        accommodation = Accommodation(capacity=4)
        assert accommodation.can_accommodate(3) is True
        assert accommodation.can_accommodate(5) is False
```

**2. GREEN**: Implement Accommodation model
- File: `bookings/domain/models.py`
- Minimal implementation:

```python
class Accommodation(models.Model):
    """Domain entity representing a housing unit available for booking"""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accommodations'

    def can_accommodate(self, group_size: int) -> bool:
        """Check if accommodation can fit the group"""
        return self.capacity >= group_size

    def __str__(self):
        return f"{self.name} (capacity: {self.capacity})"
```

**3. REFACTOR**: Add domain logic and validation
- Add `AccommodationRepository` interface
- Implement pricing calculations
- Add availability status methods
- Extract business rules to domain services

**4. QA**: Verify phase completion
- [ ] All Accommodation tests pass
- [ ] Migration created and applied
- [ ] Domain methods implement business logic
- [ ] Repository pattern consistent with Booker

---

### Phase 3: DateRange Value Object

**Objective**: Create immutable DateRange value object with validation and overlap detection.

#### TDD Cycle:

**1. RED**: Write failing tests for DateRange value object
- Test file: `tests/unit/domain/test_value_objects.py`
- Expected failures:
  - DateRange class doesn't exist
  - Validation logic missing
  - Overlap detection not implemented

```python
# tests/unit/domain/test_value_objects.py
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
```

**2. GREEN**: Implement DateRange value object
- File: `bookings/domain/value_objects.py`
- Minimal implementation:

```python
from dataclasses import dataclass
from datetime import date
from typing import Any

@dataclass(frozen=True)
class DateRange:
    """Value object representing an immutable date range"""

    start_date: date
    end_date: date

    def __post_init__(self):
        """Validate date range on creation"""
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")

    def overlaps(self, other: 'DateRange') -> bool:
        """Check if this date range overlaps with another"""
        return (
            self.start_date < other.end_date and
            other.start_date < self.end_date
        )

    def contains_date(self, check_date: date) -> bool:
        """Check if a specific date falls within this range"""
        return self.start_date <= check_date < self.end_date

    def duration_days(self) -> int:
        """Calculate the number of days in the range"""
        return (self.end_date - self.start_date).days
```

**3. REFACTOR**: Add utility methods
- Add `contains()` method for date inclusion
- Add `duration()` for calculating nights
- Add comparison operators
- Extract date validation to separate validator

**4. QA**: Verify phase completion
- [ ] All DateRange tests pass
- [ ] Value object is immutable
- [ ] Overlap logic correct for all edge cases
- [ ] No database dependencies (pure domain)

---

### Phase 4: Booking Domain Model (Basic)

**Objective**: Implement Booking entity with basic fields and relationships.

#### TDD Cycle:

**1. RED**: Write failing tests for Booking entity
- Test file: `tests/unit/domain/test_booking.py`
- Expected failures:
  - Booking model doesn't exist
  - Foreign key relationships missing
  - Date validation not enforced

```python
# tests/unit/domain/test_booking.py
class TestBookingEntity:
    def test_create_booking_with_valid_data(self, booker, accommodation):
        """Booking can be created with all required fields"""
        booking = Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 10),
            number_of_guests=4
        )
        assert booking.accommodation == accommodation
        assert booking.booker == booker
        assert booking.duration_nights() == 9

    def test_booking_end_date_must_be_after_start_date(self):
        """Database check constraint enforces valid date range"""
        with pytest.raises(IntegrityError):
            Booking.objects.create(
                accommodation=accommodation,
                booker=booker,
                start_date=date(2025, 6, 10),
                end_date=date(2025, 6, 1),
                number_of_guests=2
            )

    def test_booking_guests_cannot_exceed_capacity(self, booker, accommodation):
        """Domain validation prevents overbooking capacity"""
        accommodation.capacity = 4
        with pytest.raises(ValidationError):
            booking = Booking(
                accommodation=accommodation,
                booker=booker,
                start_date=date(2025, 6, 1),
                end_date=date(2025, 6, 10),
                number_of_guests=6
            )
            booking.full_clean()
```

**2. GREEN**: Implement Booking model (without constraints)
- File: `bookings/domain/models.py`
- Minimal implementation:

```python
class Booking(models.Model):
    """Domain aggregate root for accommodation reservations"""

    id = models.AutoField(primary_key=True)
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    booker = models.ForeignKey(
        Booker,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_guests = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F('start_date')),
                name='end_date_after_start_date'
            )
        ]

    def clean(self):
        """Domain validation logic"""
        super().clean()
        if self.number_of_guests > self.accommodation.capacity:
            raise ValidationError(
                f"Number of guests ({self.number_of_guests}) exceeds "
                f"accommodation capacity ({self.accommodation.capacity})"
            )

    def duration_nights(self) -> int:
        """Calculate number of nights for the booking"""
        return (self.end_date - self.start_date).days

    def __str__(self):
        return f"Booking {self.id}: {self.accommodation.name} ({self.start_date} - {self.end_date})"
```

**3. REFACTOR**: Extract domain logic
- Create `BookingService` for domain operations
- Add state transitions (pending → confirmed → cancelled)
- Implement `BookingRepository`
- Extract pricing calculation logic

**4. QA**: Verify phase completion
- [ ] All basic Booking tests pass
- [ ] Check constraint enforces date validation
- [ ] Foreign key relationships working
- [ ] Domain validation in `clean()` method

---

### Phase 5: PostgreSQL Exclusion Constraint

**Objective**: Implement database-level exclusion constraint to prevent overlapping bookings.

#### TDD Cycle:

**1. RED**: Write failing tests for overlap prevention
- Test file: `tests/integration/test_booking_constraints.py`
- Expected failures:
  - Overlapping bookings are allowed (before constraint)
  - Database doesn't prevent concurrent inserts

```python
# tests/integration/test_booking_constraints.py
@pytest.mark.django_db
class TestBookingOverlapConstraint:
    def test_cannot_create_overlapping_bookings(self, accommodation, booker):
        """PostgreSQL exclusion constraint prevents overlapping bookings"""
        # Create first booking
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 10),
            number_of_guests=2
        )

        # Attempt overlapping booking - should fail
        with pytest.raises(IntegrityError) as exc_info:
            Booking.objects.create(
                accommodation=accommodation,
                booker=booker,
                start_date=date(2025, 6, 5),
                end_date=date(2025, 6, 15),
                number_of_guests=2
            )

        assert 'bookings_no_overlap_excl' in str(exc_info.value)

    def test_adjacent_bookings_allowed(self, accommodation, booker):
        """Adjacent bookings (no overlap) are allowed"""
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 10),
            number_of_guests=2
        )

        # Same day checkout/checkin is allowed (end is exclusive)
        booking2 = Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2025, 6, 10),
            end_date=date(2025, 6, 20),
            number_of_guests=2
        )

        assert booking2.id is not None

    def test_different_accommodations_can_overlap(self, booker):
        """Same dates are allowed for different accommodations"""
        acc1 = Accommodation.objects.create(name="House 1", capacity=4, price_per_night=100)
        acc2 = Accommodation.objects.create(name="House 2", capacity=4, price_per_night=100)

        Booking.objects.create(
            accommodation=acc1,
            booker=booker,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 10),
            number_of_guests=2
        )

        booking2 = Booking.objects.create(
            accommodation=acc2,
            booker=booker,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 10),
            number_of_guests=2
        )

        assert booking2.id is not None
```

**2. GREEN**: Implement PostgreSQL exclusion constraint
- File: `bookings/migrations/000X_add_exclusion_constraint.py`
- Custom migration with raw SQL:

```python
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '000X_booking_model'),
    ]

    operations = [
        # Ensure btree_gist extension is enabled
        migrations.RunSQL(
            sql='CREATE EXTENSION IF NOT EXISTS btree_gist;',
            reverse_sql='DROP EXTENSION IF EXISTS btree_gist;'
        ),

        # Add exclusion constraint for overlapping date ranges
        migrations.RunSQL(
            sql="""
                ALTER TABLE bookings
                ADD CONSTRAINT bookings_no_overlap_excl
                EXCLUDE USING gist (
                    accommodation_id WITH =,
                    daterange(start_date, end_date, '[)') WITH &&
                )
                WHERE (status != 'cancelled');
            """,
            reverse_sql="""
                ALTER TABLE bookings
                DROP CONSTRAINT IF EXISTS bookings_no_overlap_excl;
            """
        ),
    ]
```

**3. REFACTOR**: Add index optimization
- Create additional indexes for query performance
- Add partial index for active bookings
- Document constraint behavior in model

```python
class Booking(models.Model):
    # ... existing fields ...

    class Meta:
        db_table = 'bookings'
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F('start_date')),
                name='end_date_after_start_date'
            )
            # Note: Exclusion constraint added via raw SQL migration
            # EXCLUDE USING gist (accommodation_id WITH =, daterange(start_date, end_date) WITH &&)
        ]
        indexes = [
            models.Index(fields=['accommodation', 'start_date', 'end_date']),
            models.Index(fields=['booker', 'created_at']),
            models.Index(fields=['status', 'start_date']),
        ]
```

**4. QA**: Verify phase completion
- [ ] All constraint tests pass
- [ ] Exclusion constraint blocks overlaps
- [ ] Adjacent bookings work correctly
- [ ] Different accommodations can have same dates
- [ ] Cancelled bookings don't block dates
- [ ] Performance tested with concurrent inserts

---

### Phase 6: Booking Domain Service & Validation

**Objective**: Implement domain service for booking validation and availability checking.

#### TDD Cycle:

**1. RED**: Write failing tests for domain service
- Test file: `tests/unit/domain/test_booking_service.py`
- Expected failures:
  - BookingService doesn't exist
  - Validation methods missing
  - Availability check not implemented

```python
# tests/unit/domain/test_booking_service.py
class TestBookingService:
    def test_validate_booking_dates(self):
        """Service validates booking date range"""
        service = BookingService()
        date_range = DateRange(date(2025, 6, 1), date(2025, 6, 10))

        assert service.validate_date_range(date_range) is True

        # Past dates invalid
        past_range = DateRange(date(2024, 1, 1), date(2024, 1, 10))
        with pytest.raises(BookingValidationError):
            service.validate_date_range(past_range)

    def test_check_availability(self, accommodation):
        """Service checks accommodation availability for date range"""
        service = BookingService()

        # No existing bookings
        date_range = DateRange(date(2025, 6, 1), date(2025, 6, 10))
        assert service.is_available(accommodation, date_range) is True

        # Create booking
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2025, 6, 5),
            end_date=date(2025, 6, 15),
            number_of_guests=2
        )

        # Overlapping range not available
        assert service.is_available(accommodation, date_range) is False

        # Non-overlapping range available
        future_range = DateRange(date(2025, 7, 1), date(2025, 7, 10))
        assert service.is_available(accommodation, future_range) is True

    def test_create_booking_with_validation(self, accommodation, booker):
        """Service creates booking with full validation"""
        service = BookingService()

        booking = service.create_booking(
            accommodation=accommodation,
            booker=booker,
            date_range=DateRange(date(2025, 6, 1), date(2025, 6, 10)),
            number_of_guests=2
        )

        assert booking.id is not None
        assert booking.status == 'pending'
```

**2. GREEN**: Implement BookingService
- File: `bookings/domain/services.py`
- Minimal implementation:

```python
from django.db import transaction
from django.utils import timezone
from .models import Booking, Accommodation
from .value_objects import DateRange
from .exceptions import BookingValidationError

class BookingService:
    """Domain service for booking operations"""

    def validate_date_range(self, date_range: DateRange) -> bool:
        """Validate booking date range against business rules"""
        today = timezone.now().date()

        if date_range.start_date < today:
            raise BookingValidationError("Cannot book dates in the past")

        if date_range.duration_days() < 1:
            raise BookingValidationError("Booking must be at least 1 night")

        if date_range.duration_days() > 365:
            raise BookingValidationError("Booking cannot exceed 365 nights")

        return True

    def is_available(self, accommodation: Accommodation, date_range: DateRange) -> bool:
        """Check if accommodation is available for the date range"""
        overlapping = Booking.objects.filter(
            accommodation=accommodation,
            start_date__lt=date_range.end_date,
            end_date__gt=date_range.start_date,
            status__in=['pending', 'confirmed']
        ).exists()

        return not overlapping

    @transaction.atomic
    def create_booking(
        self,
        accommodation: Accommodation,
        booker,
        date_range: DateRange,
        number_of_guests: int
    ) -> Booking:
        """Create a new booking with full validation"""
        # Validate date range
        self.validate_date_range(date_range)

        # Check availability
        if not self.is_available(accommodation, date_range):
            raise BookingValidationError(
                f"Accommodation not available from {date_range.start_date} to {date_range.end_date}"
            )

        # Validate capacity
        if number_of_guests > accommodation.capacity:
            raise BookingValidationError(
                f"Number of guests ({number_of_guests}) exceeds capacity ({accommodation.capacity})"
            )

        # Create booking
        booking = Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date_range.start_date,
            end_date=date_range.end_date,
            number_of_guests=number_of_guests,
            status='pending'
        )

        return booking
```

**3. REFACTOR**: Extract validation strategies
- Create separate validators for different rules
- Implement specification pattern for availability
- Add booking policies (cancellation, modification)
- Create domain events for booking lifecycle

**4. QA**: Verify phase completion
- [ ] All service tests pass
- [ ] Validation prevents invalid bookings
- [ ] Availability check accurate
- [ ] Transaction safety ensured
- [ ] Domain exceptions properly raised

---

### Phase 7: REST API - Booking Creation

**Objective**: Implement API endpoint to create bookings with proper validation and error handling.

#### TDD Cycle:

**1. RED**: Write failing API tests for booking creation
- Test file: `tests/api/test_booking_api.py`
- Expected failures:
  - Endpoint doesn't exist
  - Validation not applied
  - Error responses incorrect

```python
# tests/api/test_booking_api.py
@pytest.mark.django_db
class TestBookingCreateAPI:
    def test_create_booking_success(self, api_client, accommodation, booker):
        """POST /api/bookings/ creates a new booking"""
        url = reverse('booking-list')
        data = {
            'accommodation_id': accommodation.id,
            'booker_id': booker.id,
            'start_date': '2025-06-01',
            'end_date': '2025-06-10',
            'number_of_guests': 2
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == 201
        assert response.data['accommodation_id'] == accommodation.id
        assert response.data['status'] == 'pending'
        assert 'id' in response.data

    def test_create_booking_overlapping_dates_fails(self, api_client, accommodation, booker):
        """Overlapping booking returns 409 Conflict"""
        # Create first booking
        Booking.objects.create(
            accommodation=accommodation,
            booker=booker,
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 10),
            number_of_guests=2
        )

        url = reverse('booking-list')
        data = {
            'accommodation_id': accommodation.id,
            'booker_id': booker.id,
            'start_date': '2025-06-05',
            'end_date': '2025-06-15',
            'number_of_guests': 2
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == 409
        assert 'not available' in response.data['error'].lower()

    def test_create_booking_validation_errors(self, api_client, accommodation, booker):
        """Invalid data returns 400 Bad Request"""
        url = reverse('booking-list')
        data = {
            'accommodation_id': accommodation.id,
            'booker_id': booker.id,
            'start_date': '2025-06-10',
            'end_date': '2025-06-01',  # End before start
            'number_of_guests': 2
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == 400
```

**2. GREEN**: Implement booking creation endpoint
- File: `bookings/api/views.py`
- Minimal implementation using Django REST Framework:

```python
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import IntegrityError
from ..domain.services import BookingService
from ..domain.value_objects import DateRange
from ..domain.exceptions import BookingValidationError
from .serializers import BookingSerializer, BookingCreateSerializer

@api_view(['POST'])
def create_booking(request):
    """Create a new booking"""
    serializer = BookingCreateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        service = BookingService()
        date_range = DateRange(
            serializer.validated_data['start_date'],
            serializer.validated_data['end_date']
        )

        booking = service.create_booking(
            accommodation=serializer.validated_data['accommodation'],
            booker=serializer.validated_data['booker'],
            date_range=date_range,
            number_of_guests=serializer.validated_data['number_of_guests']
        )

        response_serializer = BookingSerializer(booking)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    except BookingValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)

    except IntegrityError as e:
        # PostgreSQL exclusion constraint violation
        return Response(
            {'error': 'Accommodation not available for selected dates'},
            status=status.HTTP_409_CONFLICT
        )
```

**3. REFACTOR**: Use ViewSets and proper DRF patterns
- Convert to ViewSet with proper actions
- Add permission classes
- Implement pagination
- Add filtering and search

```python
# bookings/api/views.py (refactored)
from rest_framework import viewsets, status
from rest_framework.response import Response

class BookingViewSet(viewsets.ModelViewSet):
    """API endpoint for booking management"""

    queryset = Booking.objects.select_related('accommodation', 'booker')
    serializer_class = BookingSerializer

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

        except BookingValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
        except IntegrityError:
            return Response(
                {'error': 'Accommodation not available for selected dates'},
                status=status.HTTP_409_CONFLICT
            )
```

**4. QA**: Verify phase completion
- [ ] All API tests pass
- [ ] Proper HTTP status codes returned
- [ ] Error messages are clear
- [ ] Input validation working
- [ ] Domain service properly invoked

---

### Phase 8: REST API - Booking List

**Objective**: Implement API endpoint to list bookings with accommodation details.

#### TDD Cycle:

**1. RED**: Write failing tests for booking list endpoint
- Test file: `tests/api/test_booking_list_api.py`
- Expected failures:
  - List endpoint doesn't exist
  - Accommodation details missing
  - Filtering not working

```python
# tests/api/test_booking_list_api.py
@pytest.mark.django_db
class TestBookingListAPI:
    def test_list_bookings(self, api_client, bookings):
        """GET /api/bookings/ returns list of bookings"""
        url = reverse('booking-list')
        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data['results']) == len(bookings)

    def test_booking_includes_accommodation_details(self, api_client, booking):
        """Booking response includes accommodation name and capacity"""
        url = reverse('booking-list')
        response = api_client.get(url)

        booking_data = response.data['results'][0]
        assert 'accommodation_name' in booking_data
        assert 'accommodation_capacity' in booking_data
        assert booking_data['accommodation_name'] == booking.accommodation.name
        assert booking_data['accommodation_capacity'] == booking.accommodation.capacity

    def test_filter_bookings_by_accommodation(self, api_client, bookings):
        """Can filter bookings by accommodation ID"""
        accommodation = bookings[0].accommodation
        url = reverse('booking-list')
        response = api_client.get(url, {'accommodation_id': accommodation.id})

        assert response.status_code == 200
        for booking in response.data['results']:
            assert booking['accommodation_id'] == accommodation.id

    def test_filter_bookings_by_date_range(self, api_client, bookings):
        """Can filter bookings by date range"""
        url = reverse('booking-list')
        response = api_client.get(url, {
            'start_date': '2025-06-01',
            'end_date': '2025-06-30'
        })

        assert response.status_code == 200
        # Verify results are within date range
```

**2. GREEN**: Implement booking list endpoint
- File: `bookings/api/serializers.py`
- Implement serializers with nested data:

```python
from rest_framework import serializers
from ..domain.models import Booking, Accommodation, Booker

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
```

**3. REFACTOR**: Add filtering and optimization
- Implement `django-filter` for advanced filtering
- Add `select_related()` for query optimization
- Implement pagination
- Add ordering options

```python
# bookings/api/filters.py
from django_filters import rest_framework as filters
from ..domain.models import Booking

class BookingFilter(filters.FilterSet):
    """Filter set for booking queries"""

    accommodation_id = filters.NumberFilter(field_name='accommodation__id')
    start_date = filters.DateFilter(field_name='start_date', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='end_date', lookup_expr='lte')
    status = filters.ChoiceFilter(choices=Booking._meta.get_field('status').choices)

    class Meta:
        model = Booking
        fields = ['accommodation_id', 'start_date', 'end_date', 'status']

# bookings/api/views.py (updated)
class BookingViewSet(viewsets.ModelViewSet):
    """API endpoint for booking management"""

    queryset = Booking.objects.select_related(
        'accommodation', 'booker'
    ).order_by('-created_at')

    serializer_class = BookingSerializer
    filterset_class = BookingFilter
    ordering_fields = ['start_date', 'created_at', 'accommodation__name']
    search_fields = ['booker__name', 'accommodation__name']
```

**4. QA**: Verify phase completion
- [ ] All list API tests pass
- [ ] Accommodation details included in response
- [ ] Filtering works correctly
- [ ] Pagination implemented
- [ ] Query optimization (N+1 prevented)

---

### Phase 9: API Documentation & OpenAPI

**Objective**: Generate comprehensive API documentation using drf-spectacular.

#### TDD Cycle:

**1. RED**: Write tests for API schema
- Test file: `tests/api/test_api_schema.py`
- Expected failures:
  - Schema endpoint doesn't exist
  - Documentation incomplete

```python
# tests/api/test_api_schema.py
@pytest.mark.django_db
class TestAPISchema:
    def test_openapi_schema_available(self, api_client):
        """OpenAPI schema is accessible"""
        url = '/api/schema/'
        response = api_client.get(url)

        assert response.status_code == 200
        assert 'openapi' in response.data

    def test_swagger_ui_available(self, client):
        """Swagger UI documentation is accessible"""
        url = '/api/docs/'
        response = client.get(url)

        assert response.status_code == 200
```

**2. GREEN**: Configure drf-spectacular
- Install: `drf-spectacular`
- Configure in `settings.py`
- Add schema endpoints

**3. REFACTOR**: Enhance documentation
- Add detailed schema annotations
- Include example requests/responses
- Document error codes

**4. QA**: Verify phase completion
- [ ] OpenAPI schema generated
- [ ] Swagger UI accessible
- [ ] All endpoints documented
- [ ] Examples included

---

## Success Criteria

### Functional Requirements
- [ ] Booker model with group size tracking
- [ ] Accommodation model with capacity validation
- [ ] Booking model with date range validation
- [ ] PostgreSQL exclusion constraint prevents overlapping bookings
- [ ] DateRange value object with immutability
- [ ] Domain services handle business logic
- [ ] REST API for booking creation
- [ ] REST API for booking listing with accommodation details
- [ ] Comprehensive test coverage (>90%)

### Technical Requirements
- [ ] DDD architecture (entities, value objects, services, repositories)
- [ ] PostgreSQL `btree_gist` extension enabled
- [ ] Exclusion constraint using `daterange` and `gist` index
- [ ] Check constraint validates end_date > start_date
- [ ] Foreign key constraints maintain referential integrity
- [ ] Query optimization with `select_related()`
- [ ] Proper HTTP status codes (200, 201, 400, 409)
- [ ] Transaction safety in domain services
- [ ] API documentation with OpenAPI/Swagger

### Quality Requirements
- [ ] All tests pass (unit, integration, API)
- [ ] Code follows DDD patterns
- [ ] Database constraints enforce business rules
- [ ] Clear error messages for validation failures
- [ ] No N+1 query problems
- [ ] Immutable value objects
- [ ] Proper separation of concerns (domain/infrastructure/API)

---

## Testing Commands

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/api/

# Run with coverage
pytest --cov=bookings --cov-report=html

# Run specific test file
pytest tests/integration/test_booking_constraints.py -v

# Run with database inspection
pytest --reuse-db -v

# Check database constraint in PostgreSQL
psql -d reservation_db -c "\d bookings"
psql -d reservation_db -c "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'bookings'::regclass;"
```

---

## PostgreSQL Constraint Details

### Exclusion Constraint Syntax
```sql
ALTER TABLE bookings
ADD CONSTRAINT bookings_no_overlap_excl
EXCLUDE USING gist (
    accommodation_id WITH =,
    daterange(start_date, end_date, '[)') WITH &&
)
WHERE (status != 'cancelled');
```

### How It Works
- `EXCLUDE USING gist`: Uses GiST (Generalized Search Tree) index
- `accommodation_id WITH =`: Same accommodation ID
- `daterange(start_date, end_date, '[)') WITH &&`: Date ranges that overlap
- `[)`: Left-inclusive, right-exclusive (checkout day available for next booking)
- `WHERE (status != 'cancelled')`: Cancelled bookings don't block dates

### Benefits
- **Database-level enforcement**: Cannot be bypassed by application code
- **Concurrency safety**: Handles race conditions automatically
- **Performance**: GiST index enables efficient overlap queries
- **Data integrity**: Guaranteed by PostgreSQL transaction system

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         API Layer                            │
│  ┌────────────────────┐  ┌─────────────────────────────┐   │
│  │ BookingViewSet     │  │ Serializers                  │   │
│  │ - create()         │  │ - BookingSerializer          │   │
│  │ - list()           │  │ - BookingCreateSerializer    │   │
│  └────────────────────┘  └─────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                      Application Layer                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ BookingService (Domain Service)                        │ │
│  │ - create_booking()                                     │ │
│  │ - is_available()                                       │ │
│  │ - validate_date_range()                                │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                        Domain Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Booker       │  │ Accommodation│  │ Booking          │  │
│  │ (Entity)     │  │ (Entity)     │  │ (Aggregate Root) │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ DateRange (Value Object)                              │  │
│  │ - immutable, overlap detection                        │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                   Infrastructure Layer                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ PostgreSQL Database                                    │ │
│  │ - Exclusion Constraint (btree_gist)                    │ │
│  │ - Check Constraints                                    │ │
│  │ - Foreign Key Constraints                              │ │
│  │ - Indexes                                              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

*Phased TDD Development Plan*
*Focus: DDD Architecture • PostgreSQL Constraints • Data Integrity*
