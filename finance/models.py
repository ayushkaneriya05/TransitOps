from django.db import models
from django.core.validators import MinValueValidator
from fleet.models import Vehicle
from operations.models import Trip


class FuelLog(models.Model):
    """Log for fuel consumed by a vehicle."""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_logs')
    date = models.DateField()
    liters = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    cost = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_fuellog'
        ordering = ['-date']

    def __str__(self):
        return f"Fuel — {self.liters}L for {self.vehicle.name} ({self.date})"


class Expense(models.Model):
    """Financial record: tolls and other costs."""

    class Category(models.TextChoices):
        TOLL = 'toll', 'Toll'
        OTHER = 'other', 'Other'

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='expenses')
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.TOLL)
    cost = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_expense'
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_category_display()} — ₹{self.cost} — {self.vehicle.name} ({self.date})"
