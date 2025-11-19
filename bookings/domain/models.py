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
