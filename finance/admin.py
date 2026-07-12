from django.contrib import admin
from .models import Expense, FuelLog


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'category', 'cost', 'date', 'trip')
    list_filter = ('category', 'date')


@admin.register(FuelLog)
class FuelLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'liters', 'cost', 'date')
    list_filter = ('date',)
