# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2025-11-20

### Added - Critical Improvements

#### Concurrency & Data Integrity
- **PostgreSQL Exclusion Constraint** (`0005_add_exclusion_constraint.py`)
  - Implemented database-level overlap prevention using `btree_gist` extension
  - Prevents race conditions that could create overlapping bookings
  - Constraint: `bookings_no_overlap` excludes overlapping date ranges for same accommodation
  - Only applies to active bookings (pending/confirmed), cancelled bookings don't block

- **Optimistic Locking** (`0006_booking_version.py`)
  - Added `version` field to Booking model
  - Prevents lost updates when multiple users modify same booking
  - Implements version-based concurrency control

#### Architecture Improvements
- **Decoupled Domain Services**
  - Refactored `BookingService` to use repository pattern
  - Removed direct Django ORM dependencies from domain layer
  - Constructor now requires repository dependencies (dependency injection)
  - Breaking change: `BookingService()` → `BookingService(booking_repo, accommodation_repo, booker_repo)`

- **Repository Pattern Fully Implemented**
  - Domain services now interact with repositories instead of Django models directly
  - Enables easier testing with mock repositories
  - Improves separation of concerns

- **Dependency Injection in API Views**
  - `BookingViewSet` now initializes repositories in `__init__`
  - Services are instantiated with repository dependencies
  - Better testability and flexibility

#### Testing Enhancements
- **Repository Unit Tests** (`tests/unit/infrastructure/test_repositories.py`)
  - Comprehensive tests for all repository methods
  - Tests for `DjangoBookerRepository`, `DjangoAccommodationRepository`, `DjangoBookingRepository`
  - Covers get, save, find, and list operations

- **Concurrency Integration Tests** (`tests/integration/test_booking_concurrency.py`)
  - Tests concurrent booking creation attempts
  - Verifies only one booking succeeds when multiple threads race
  - Tests different accommodations and date ranges
  - Tests exclusion constraint enforcement

#### Domain Logic
- **Status Transition Validation**
  - Added `can_confirm()` and `can_cancel()` methods to Booking model
  - Added `confirm()` and `cancel()` methods with validation
  - Enforces proper state machine transitions
  - Prevents invalid status changes

#### Admin Interface
- **Comprehensive Django Admin** (`bookings/admin.py`)
  - Full admin interface for Booker, Accommodation, and Booking models
  - Custom list displays with relevant fields
  - Filtering and search capabilities
  - Color-coded status badges for bookings
  - Bulk actions: confirm/cancel bookings
  - Readonly fields for system-managed data
  - Organized fieldsets for better UX

### Changed

#### Domain Service API
- **Breaking:** `BookingService.create_booking()` signature changed
  - Old: `create_booking(accommodation, booker, date_range, number_of_guests)`
  - New: `create_booking(accommodation_id, booker_id, date_range, number_of_guests)`
  - Now accepts IDs instead of objects and loads entities via repositories

- **Breaking:** `BookingService.__init__()` now requires repositories
  - Must pass `booking_repository`, `accommodation_repository`, `booker_repository`
  - Example: `BookingService(booking_repo, accommodation_repo, booker_repo)`

#### Model Changes
- **Booking model**
  - Removed application-level overlap check from `save()` method
  - Overlap prevention now handled by database constraint
  - Added `version` field (defaults to 0)
  - Added status transition methods (`confirm()`, `cancel()`)

#### Error Handling
- **API Views**
  - Enhanced error handling for database constraint violations
  - Specific handling for `bookings_no_overlap` constraint
  - Better error messages for not found entities

### Removed
- Application-level overlap checking in `Booking.save()`
  - Was redundant with database constraint
  - Had race condition vulnerability (TOCTOU)
  - Database constraint is more reliable

### Fixed
- **Race Condition Vulnerability**
  - Fixed TOCTOU (Time-Of-Check-Time-Of-Use) bug in overlap detection
  - Concurrent booking requests can no longer create overlapping bookings
  - Database constraint provides atomic enforcement

- **Architecture Violations**
  - Fixed domain layer dependency on Django ORM
  - Domain services now properly use repository abstraction
  - Cleaner separation of concerns

### Documentation
- Updated README.md to accurately reflect exclusion constraint implementation
- Added "Recent Improvements" section highlighting enhancements
- Updated constraint examples with actual SQL

### Migration Guide

#### For Developers Using BookingService

**Before:**
```python
from bookings.domain.services import BookingService

service = BookingService()
booking = service.create_booking(
    accommodation=accommodation_obj,
    booker=booker_obj,
    date_range=date_range,
    number_of_guests=2
)
```

**After:**
```python
from bookings.domain.services import BookingService
from bookings.infrastructure.repositories import (
    DjangoBookingRepository,
    DjangoAccommodationRepository,
    DjangoBookerRepository,
)

# Initialize repositories
booking_repo = DjangoBookingRepository()
accommodation_repo = DjangoAccommodationRepository()
booker_repo = DjangoBookerRepository()

# Create service with dependencies
service = BookingService(booking_repo, accommodation_repo, booker_repo)

# Call with IDs instead of objects
booking = service.create_booking(
    accommodation_id=accommodation_id,
    booker_id=booker_id,
    date_range=date_range,
    number_of_guests=2
)
```

#### Database Migration

After pulling these changes, run:

```bash
# Apply migrations (will create exclusion constraint)
uv run python manage.py migrate

# Note: Migration 0005 requires PostgreSQL btree_gist extension
# The migration will enable it automatically
```

#### Test Updates

Tests using `BookingService` need to be updated to pass repositories:

```python
# Old
service = BookingService()

# New
booking_repo = DjangoBookingRepository()
accommodation_repo = DjangoAccommodationRepository()
booker_repo = DjangoBookerRepository()
service = BookingService(booking_repo, accommodation_repo, booker_repo)
```

### Security Improvements
- Database-level enforcement prevents bypassing application logic
- Optimistic locking prevents lost update anomalies
- Proper state machine enforcement for booking status

### Performance
- No performance degradation from exclusion constraint
- Existing composite index on (accommodation, start_date, end_date) supports constraint efficiently
- Repository pattern doesn't add measurable overhead

### Breaking Changes Summary
1. `BookingService` constructor now requires three repository parameters
2. `BookingService.create_booking()` takes IDs instead of model instances
3. `validate_date_range()` returns `None` instead of `True` (raises exception on error)

---

## Version History

- **[Unreleased]** - Major architectural improvements, concurrency fixes, full test coverage
- **v0.1.0** - Initial implementation with DDD architecture and REST API
