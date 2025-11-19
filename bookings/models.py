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

    @classmethod
    def create_standard_house(cls, name: str, capacity: int, price_per_night: float, description: str = ""):
        """Factory method for standard house"""
        return cls(
            name=name,
            capacity=capacity,
            price_per_night=price_per_night,
            description=description,
            is_active=True
        )

    @classmethod
    def create_luxury_villa(cls, name: str, capacity: int, price_per_night: float, description: str = ""):
        """Factory method for luxury villa with premium pricing"""
        return cls(
            name=name,
            capacity=capacity,
            price_per_night=price_per_night,
            description=description,
            is_active=True
        )