# Reservation System

A housing reservation management system built with Django, PostgreSQL, and Domain-Driven Design (DDD) principles.

## Features

- **Domain-Driven Design**: Clean architecture with entities, value objects, and domain services
- **PostgreSQL Constraints**: Database-level enforcement prevents overlapping bookings using `btree_gist` exclusion constraints
- **Test-Driven Development**: Comprehensive test coverage with pytest
- **REST API**: Full API for managing bookings with Django REST Framework
- **Type Safety**: Type hints and mypy validation

## Domain Model

### Entities

- **Booker**: Represents a group of persons making a reservation
  - Name, email, phone, group size
  - Factory methods for common patterns (single person, family)

- **Accommodation**: Represents a housing unit available for booking
  - Name, description, capacity, price per night
  - Capacity validation and availability checking

- **Booking**: Aggregate root for reservations
  - Links accommodation with booker for specific dates
  - Status tracking (pending, confirmed, cancelled)
  - Automatic overlap prevention via PostgreSQL constraints

### Value Objects

- **DateRange**: Immutable date range with overlap detection

### Domain Services

- **BookingService**: Business logic for creating and validating bookings
  - Date range validation
  - Availability checking
  - Capacity enforcement

## PostgreSQL Exclusion Constraints

The system uses PostgreSQL's exclusion constraints with the `btree_gist` extension to prevent overlapping bookings at the database level:

```sql
ALTER TABLE bookings
ADD CONSTRAINT bookings_no_overlap
EXCLUDE USING gist (
    accommodation_id WITH =,
    daterange(start_date, end_date, '[)') WITH &&
)
WHERE (status IN ('pending', 'confirmed'));
```

This ensures:

- **No two active bookings can overlap** for the same accommodation
- **Database-level enforcement** - cannot be bypassed by application code
- **Concurrency-safe** - handles race conditions reliably
- **Cancelled bookings don't block** future reservations
- **Atomic operations** - no TOCTOU (time-of-check-time-of-use) vulnerabilities

## Requirements

- Python 3.11+
- PostgreSQL 14+ (with `btree_gist` extension)
- uv (for dependency management)

## Installation

1. Install dependencies with uv:

```bash
uv sync
```

2. Set up PostgreSQL database:

```bash
createdb reservation_db
psql reservation_db -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"
```

3. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run migrations:

```bash
uv run python manage.py migrate
```

5. Create a superuser:

```bash
uv run python manage.py createsuperuser
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=bookings --cov-report=html

# Run specific test categories
uv run pytest tests/unit/          # Unit tests only
uv run pytest tests/integration/   # Integration tests only
uv run pytest tests/api/           # API tests only
```

### Code Quality

```bash
# Linting with ruff
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Type checking
uv run mypy bookings/
```

### Running the Development Server

```bash
uv run python manage.py runserver
```

## API Endpoints

### Bookings

- `POST /api/bookings/` - Create a new booking
- `GET /api/bookings/` - List all bookings
- `GET /api/bookings/{id}/` - Get booking details
- `PATCH /api/bookings/{id}/` - Update booking
- `DELETE /api/bookings/{id}/` - Cancel booking

### API Documentation

- Swagger UI: <http://localhost:8000/api/docs/>
- ReDoc: <http://localhost:8000/api/redoc/>
- OpenAPI Schema: <http://localhost:8000/api/schema/>

## Project Structure

```
reservation_system/
├── bookings/              # Main application
│   ├── domain/           # DDD domain layer
│   │   ├── models.py     # Entities (Booker, Accommodation, Booking)
│   │   ├── services.py   # Domain services
│   │   └── value_objects.py  # Value objects (DateRange)
│   ├── api/              # REST API layer
│   │   ├── views.py      # ViewSets
│   │   ├── serializers.py # DRF serializers
│   │   └── filters.py    # Query filters
│   └── migrations/       # Database migrations
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── api/             # API tests
└── reservation_system/   # Django project settings

```

## Architecture

The project follows Domain-Driven Design principles:

```
┌─────────────────────────────────────────┐
│           API Layer                     │
│  (ViewSets, Serializers, Filters)       │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│        Application Layer                │
│  (BookingService - Domain Service)      │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│          Domain Layer                   │
│  (Entities, Value Objects)              │
│  - Booker, Accommodation, Booking       │
│  - DateRange (Value Object)             │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│     Infrastructure Layer                │
│  (PostgreSQL + Constraints)             │
└─────────────────────────────────────────┘
```

## Testing Strategy

- **Unit Tests**: Test domain logic in isolation
- **Integration Tests**: Test database constraints and ORM behavior
- **API Tests**: Test endpoint behavior and error handling

All tests follow TDD methodology with RED → GREEN → REFACTOR → QA cycles.

## Recent Improvements

This codebase has been enhanced with the following architectural improvements:

### Concurrency & Data Integrity
- ✅ **PostgreSQL exclusion constraint** implemented for true database-level overlap prevention
- ✅ **Optimistic locking** via version field to prevent lost updates
- ✅ **Comprehensive concurrency tests** to verify thread-safety

### Architecture & Design
- ✅ **Decoupled domain services** from Django ORM using repository pattern
- ✅ **Dependency injection** in API views for better testability
- ✅ **Status transition validation** with proper state machine methods

### Testing & Quality
- ✅ **Repository unit tests** covering all data access operations
- ✅ **Concurrency integration tests** validating race condition handling
- ✅ **Django admin interface** for operational management

### Code Quality
- ✅ Clean separation between domain logic and infrastructure
- ✅ Type-safe interfaces with proper abstractions
- ✅ All business rules enforced at multiple layers

## License

MIT

## Contributing

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the detailed development roadmap following TDD methodology.
