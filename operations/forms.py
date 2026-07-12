from django import forms
from django.db.models import Q
from django.utils import timezone
from .models import Trip
from fleet.models import Vehicle
from drivers.models import Driver
from decimal import Decimal

FORM_INPUT_CLASS = 'form-input'


class TripCreateForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['vehicle', 'driver', 'source', 'destination', 'planned_distance', 'cargo_weight', 'revenue', 'notes']
        widgets = {
            'vehicle': forms.Select(attrs={'class': FORM_INPUT_CLASS}),
            'driver': forms.Select(attrs={'class': FORM_INPUT_CLASS}),
            'source': forms.TextInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Origin city/warehouse'}),
            'destination': forms.TextInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Destination city/warehouse'}),
            'planned_distance': forms.NumberInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Distance in km', 'min': '0.01', 'step': '0.01'}),
            'cargo_weight': forms.NumberInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Weight in kg', 'min': '0.01', 'step': '0.01'}),
            'revenue': forms.NumberInput(attrs={'class': FORM_INPUT_CLASS, 'placeholder': 'Revenue in ₹', 'min': '0', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': FORM_INPUT_CLASS, 'rows': 2, 'placeholder': 'Additional notes...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # When editing, show all non-retired vehicles/drivers; when creating, show only available
        if self.instance and self.instance.pk:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(
                Q(status=Vehicle.Status.AVAILABLE) | Q(pk=self.instance.vehicle_id)
            ).exclude(status=Vehicle.Status.RETIRED)
            self.fields['driver'].queryset = Driver.objects.filter(
                Q(status=Driver.Status.AVAILABLE, license_expiry__gte=timezone.now().date()) | Q(pk=self.instance.driver_id)
            ).exclude(status=Driver.Status.SUSPENDED)
        else:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(status=Vehicle.Status.AVAILABLE)
            self.fields['driver'].queryset = Driver.objects.filter(
                status=Driver.Status.AVAILABLE,
                license_expiry__gte=timezone.now().date()
            )

    def clean(self):
        cleaned = super().clean()
        vehicle = cleaned.get('vehicle')
        driver = cleaned.get('driver')
        cargo_weight = cleaned.get('cargo_weight')

        if not vehicle or not driver:
            return cleaned

        # Skip availability checks when editing an existing trip
        is_new = not (self.instance and self.instance.pk)

        if is_new:
            if vehicle.status != Vehicle.Status.AVAILABLE:
                self.add_error('vehicle', f'Vehicle "{vehicle.name}" is not available ({vehicle.get_status_display()}).')
            if driver.status != Driver.Status.AVAILABLE:
                self.add_error('driver', f'Driver "{driver.name}" is not available ({driver.get_status_display()}).')

        if not driver.is_license_valid:
            self.add_error('driver', f'Driver "{driver.name}" has an expired license (expired: {driver.license_expiry}).')

        if driver.status == Driver.Status.SUSPENDED:
            self.add_error('driver', f'Driver "{driver.name}" is suspended.')

        if cargo_weight and vehicle:
            if Decimal(str(cargo_weight)) > vehicle.capacity:
                self.add_error('cargo_weight', f'Exceeds vehicle capacity ({vehicle.capacity} kg).')
                
        planned_distance = cleaned.get('planned_distance')
        if planned_distance is not None and planned_distance <= 0:
            self.add_error('planned_distance', 'Planned distance must be greater than 0.')

        if driver.vehicle_category != 'all' and driver.vehicle_category != vehicle.vehicle_type:
            self.add_error('driver', f'Driver is certified for {driver.get_vehicle_category_display()}, not {vehicle.get_vehicle_type_display()}.')

        return cleaned


class TripCompleteForm(forms.Form):
    odometer_end = forms.DecimalField(
        max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': FORM_INPUT_CLASS,
            'placeholder': 'Final odometer reading in km',
            'min': '0', 'step': '0.01',
        }),
    )
    fuel_consumed = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        widget=forms.NumberInput(attrs={
            'class': FORM_INPUT_CLASS,
            'placeholder': 'Fuel consumed in liters (optional)',
            'min': '0', 'step': '0.01',
        }),
    )
    fuel_cost = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        widget=forms.NumberInput(attrs={
            'class': FORM_INPUT_CLASS,
            'placeholder': 'Total fuel cost in ₹ (optional)',
            'min': '0', 'step': '0.01',
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        fuel_consumed = cleaned_data.get('fuel_consumed')
        fuel_cost = cleaned_data.get('fuel_cost')
        
        if (fuel_consumed and not fuel_cost) or (fuel_cost and not fuel_consumed):
            raise forms.ValidationError("Both fuel consumed and fuel cost must be provided if one is.")
            
        return cleaned_data
