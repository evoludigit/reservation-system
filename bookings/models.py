from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Booker(models.Model):
    """Domain entity representing a group booking a reservation"""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    group_size = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bookers"

    def __str__(self):
        return f"{self.name} ({self.group_size} persons)"

    @classmethod
    def create_single_person(cls, name: str, email: str, phone: str):
        """Factory method for single person booker"""
        return cls(name=name, email=email, phone=phone, group_size=1)

    @classmethod
    def create_family(cls, name: str, email: str, phone: str, family_size: int):
        """Factory method for family booker"""
        return cls(name=name, email=email, phone=phone, group_size=family_size)


class Accommodation(models.Model):
    """Domain entity representing a housing unit available for booking"""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price_per_night = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accommodations"

    def can_accommodate(self, group_size: int) -> bool:
        """Check if accommodation can fit the group"""
        return self.capacity >= group_size

    def __str__(self):
        return f"{self.name} (capacity: {self.capacity})"

    @classmethod
    def create_standard_house(
        cls, name: str, capacity: int, price_per_night: float, description: str = ""
    ):
        """Factory method for standard house"""
        return cls(
            name=name,
            capacity=capacity,
            price_per_night=price_per_night,
            description=description,
            is_active=True,
        )

    @classmethod
    def create_luxury_villa(
        cls, name: str, capacity: int, price_per_night: float, description: str = ""
    ):
        """Factory method for luxury villa with premium pricing"""
        return cls(
            name=name,
            capacity=capacity,
            price_per_night=price_per_night,
            description=description,
            is_active=True,
        )


class Booking(models.Model):
    """Domain aggregate root for accommodation reservations"""

    id = models.AutoField(primary_key=True)
    accommodation = models.ForeignKey(
        Accommodation, on_delete=models.PROTECT, related_name="bookings"
    )
    booker = models.ForeignKey(Booker, on_delete=models.PROTECT, related_name="bookings")
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_guests = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        default="pending",
    )
    version = models.IntegerField(default=0)  # For optimistic locking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bookings"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gt=models.F("start_date")),
                name="end_date_after_start_date",
            )
        ]
        indexes = [
            models.Index(fields=["accommodation", "start_date", "end_date"]),
            models.Index(fields=["booker", "created_at"]),
            models.Index(fields=["status", "start_date"]),
        ]

    def clean(self):
        """Domain validation logic"""
        super().clean()
        if self.number_of_guests > self.accommodation.capacity:
            raise ValidationError(
                f"Number of guests ({self.number_of_guests}) exceeds "
                f"accommodation capacity ({self.accommodation.capacity})"
            )

    def save(self, *args, **kwargs):
        """Override save to check for overlapping bookings on non-PostgreSQL databases"""
        from django.db import IntegrityError, connection

        # On PostgreSQL, the exclusion constraint handles this
        # On other databases (SQLite, MySQL), we need application-level check
        if connection.vendor != "postgresql" and not self.pk:
            overlapping = Booking.objects.filter(
                accommodation=self.accommodation,
                start_date__lt=self.end_date,
                end_date__gt=self.start_date,
                status__in=["pending", "confirmed"],
            ).exists()
            if overlapping:
                raise IntegrityError(
                    "Overlapping booking detected for this accommodation and date range"
                )

        super().save(*args, **kwargs)

    def duration_nights(self) -> int:
        """Calculate number of nights for the booking"""
        return (self.end_date - self.start_date).days

    def can_confirm(self) -> bool:
        """Check if booking can be confirmed"""
        return self.status == "pending"

    def can_cancel(self) -> bool:
        """Check if booking can be cancelled"""
        return self.status in ["pending", "confirmed"]

    def confirm(self) -> None:
        """Confirm the booking"""
        if not self.can_confirm():
            raise ValidationError(f"Cannot confirm booking with status '{self.status}'")
        self.status = "confirmed"

    def cancel(self) -> None:
        """Cancel the booking"""
        if not self.can_cancel():
            raise ValidationError(f"Cannot cancel booking with status '{self.status}'")
        self.status = "cancelled"

    def __str__(self):
        return f"Booking {self.id}: {self.accommodation.name} ({self.start_date} - {self.end_date})"
