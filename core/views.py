from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum, F
from django.utils import timezone
from fleet.models import Vehicle, Maintenance
from drivers.models import Driver
from operations.models import Trip


@login_required
def dashboard(request):
    """Command Center — High-level fleet oversight."""
    vehicle_type = request.GET.get('vehicle_type', '')
    region = request.GET.get('region', '')

    vehicles = Vehicle.objects.exclude(status=Vehicle.Status.RETIRED)

    if vehicle_type:
        vehicles = vehicles.filter(vehicle_type=vehicle_type)
    if region:
        vehicles = vehicles.filter(region__icontains=region)

    total_vehicles = vehicles.count()
    
    # NEW KPIS
    active_vehicles = vehicles.filter(status__in=[Vehicle.Status.AVAILABLE, Vehicle.Status.ON_TRIP]).count()
    available_vehicles = vehicles.filter(status=Vehicle.Status.AVAILABLE).count()
    maintenance_vehicles = vehicles.filter(status=Vehicle.Status.IN_SHOP).count()
    
    # Trips
    vehicle_ids = vehicles.values_list('id', flat=True)
    active_trips = Trip.objects.filter(status=Trip.Status.DISPATCHED, vehicle_id__in=vehicle_ids).count()
    pending_trips = Trip.objects.filter(status=Trip.Status.DRAFT, vehicle_id__in=vehicle_ids).count()
    
    # Drivers on Duty
    drivers_on_duty = Driver.objects.filter(status__in=[Driver.Status.AVAILABLE, Driver.Status.ON_TRIP]).count()
    
    # Utilization
    on_trip_vehicles = vehicles.filter(status=Vehicle.Status.ON_TRIP).count()
    fleet_utilization = round((on_trip_vehicles / total_vehicles * 100), 1) if total_vehicles > 0 else 0

    recent_trips = (
        Trip.objects.select_related('vehicle', 'driver')
        .filter(vehicle_id__in=vehicle_ids)
        .order_by('-updated_at')[:10]
    )

    regions = Vehicle.objects.exclude(region='').values_list('region', flat=True).distinct().order_by('region')

    context = {
        'total_vehicles': total_vehicles,
        'active_vehicles': active_vehicles,
        'available_vehicles': available_vehicles,
        'maintenance_vehicles': maintenance_vehicles,
        'active_trips': active_trips,
        'pending_trips': pending_trips,
        'drivers_on_duty': drivers_on_duty,
        'fleet_utilization': fleet_utilization,
        'recent_trips': recent_trips,
        'vehicle_types': Vehicle.VehicleType.choices,
        'regions': regions,
        'selected_vehicle_type': vehicle_type,
        'selected_region': region,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def settings_view(request):
    """Page 9: Settings."""
    from django.contrib import messages
    if request.method == 'POST':
        messages.success(request, 'Settings saved successfully.')
        return redirect('core:settings')
    return render(request, 'core/settings.html')
