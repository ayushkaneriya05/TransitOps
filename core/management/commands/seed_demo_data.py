from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from fleet.models import Vehicle, Maintenance
from drivers.models import Driver
from operations.models import Trip
from finance.models import Expense, FuelLog


class Command(BaseCommand):
    help = 'Seeds demo data for all models (except users)'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing old data...')
        Maintenance.objects.all().delete()
        Expense.objects.all().delete()
        FuelLog.objects.all().delete()
        Trip.objects.all().delete()
        Vehicle.objects.all().delete()
        Driver.objects.all().delete()

        self.stdout.write('Creating Vehicles...')
        v1 = Vehicle.objects.create(
            name='Heavy Truck-01', registration_number='MH-01-AB-1234',
            vehicle_type=Vehicle.VehicleType.TRUCK, capacity=15000,
            odometer=45000, acquisition_cost=2500000, region='West',
            status=Vehicle.Status.AVAILABLE
        )
        v2 = Vehicle.objects.create(
            name='City Van-02', registration_number='GJ-04-CD-5678',
            vehicle_type=Vehicle.VehicleType.VAN, capacity=1200,
            odometer=12000, acquisition_cost=800000, region='North',
            status=Vehicle.Status.AVAILABLE
        )
        v3 = Vehicle.objects.create(
            name='Express Bike-03', registration_number='DL-01-EF-9012',
            vehicle_type=Vehicle.VehicleType.BIKE, capacity=50,
            odometer=5000, acquisition_cost=60000, region='Capital',
            status=Vehicle.Status.AVAILABLE
        )

        self.stdout.write('Creating Drivers...')
        d1 = Driver.objects.create(
            name='Ramesh Kumar', license_number='LIC-TRK-1001',
            license_expiry=timezone.now().date() + timedelta(days=300),
            vehicle_category=Driver.VehicleCategory.TRUCK, phone='+91-9876543210',
            status=Driver.Status.AVAILABLE, safety_score=95.5
        )
        d2 = Driver.objects.create(
            name='Suresh Singh', license_number='LIC-VAN-2002',
            license_expiry=timezone.now().date() + timedelta(days=150),
            vehicle_category=Driver.VehicleCategory.VAN, phone='+91-8765432109',
            status=Driver.Status.AVAILABLE, safety_score=88.0
        )
        d3 = Driver.objects.create(
            name='Mahesh Sharma', license_number='LIC-BIK-3003',
            license_expiry=timezone.now().date() + timedelta(days=60),
            vehicle_category=Driver.VehicleCategory.BIKE, phone='+91-7654321098',
            status=Driver.Status.AVAILABLE, safety_score=99.0
        )

        self.stdout.write('Creating Trips...')
        t1 = Trip.objects.create(
            vehicle=v1, driver=d1, source='Mumbai', destination='Pune',
            planned_distance=150, cargo_weight=10000, revenue=15000,
            status=Trip.Status.COMPLETED, odometer_start=44850, odometer_end=45000,
            notes='On time delivery.'
        )
        
        t2 = Trip.objects.create(
            vehicle=v2, driver=d2, source='Ahmedabad', destination='Surat',
            planned_distance=280, cargo_weight=800, revenue=5000,
            status=Trip.Status.DISPATCHED, odometer_start=12000,
            notes='En route.'
        )
        v2.status = Vehicle.Status.ON_TRIP
        v2.save()
        d2.status = Driver.Status.ON_TRIP
        d2.save()
        
        t3 = Trip.objects.create(
            vehicle=v3, driver=d3, source='Delhi', destination='Noida',
            planned_distance=25, cargo_weight=10, revenue=500,
            status=Trip.Status.DRAFT,
            notes='Pending dispatch.'
        )

        self.stdout.write('Creating Fuel Logs & Expenses...')
        FuelLog.objects.create(
            vehicle=v1, date=timezone.now().date() - timedelta(days=1),
            liters=50.5, cost=4500.00
        )
        Expense.objects.create(
            vehicle=v1, trip=t1, category=Expense.Category.TOLL,
            cost=350.00, date=timezone.now().date() - timedelta(days=1),
            notes='Mumbai Pune Expressway Toll'
        )
        Expense.objects.create(
            vehicle=v2, category=Expense.Category.OTHER,
            cost=1200.00, date=timezone.now().date() - timedelta(days=5),
            notes='Parking pass'
        )

        self.stdout.write('Creating Maintenance Logs...')
        Maintenance.objects.create(
            vehicle=v1, service_type=Maintenance.ServiceType.OIL_CHANGE,
            description='Routine oil and filter change',
            cost=2500.00, date=timezone.now().date() - timedelta(days=15),
            is_resolved=True
        )
        m2 = Maintenance.objects.create(
            vehicle=v3, service_type=Maintenance.ServiceType.TIRE_ROTATION,
            description='Rear tire flat',
            cost=800.00, date=timezone.now().date(),
            is_resolved=False
        )
        v3.status = Vehicle.Status.IN_SHOP
        v3.save()

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
