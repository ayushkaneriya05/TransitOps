import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, OuterRef, Subquery, Value, DecimalField
from django.db.models.functions import Coalesce
from .models import Expense, FuelLog
from .forms import ExpenseForm, FuelLogForm
from fleet.models import Vehicle, Maintenance
from operations.models import Trip
from core.decorators import role_required
from core.audit import log_creation


def _htmx_success_row(request, template, context, table_id, toast_msg, swap='afterbegin'):
    resp = render(request, template, context)
    resp['HX-Retarget'] = f'#{table_id}'
    resp['HX-Reswap'] = swap
    resp['HX-Trigger'] = json.dumps({
        'showToast': {'message': toast_msg, 'level': 'success'},
        'closeModal': True,
    })
    return resp


def _htmx_error_form(request, template, context):
    return render(request, template, context)


@login_required
def expense_list(request):
    """Page 6: Completed Trips, Expenses & Fuel Logging."""
    category_filter = request.GET.get('category', '')
    expenses = Expense.objects.select_related('vehicle', 'trip').all()
    if category_filter:
        expenses = expenses.filter(category=category_filter)

    completed_trips = Trip.objects.filter(status=Trip.Status.COMPLETED).select_related('vehicle', 'driver').order_by('-updated_at')[:10]

    fuel_sq = FuelLog.objects.filter(vehicle=OuterRef('pk')).values('vehicle').annotate(total=Sum('cost')).values('total')
    maint_sq = Maintenance.objects.filter(vehicle=OuterRef('pk')).values('vehicle').annotate(total=Sum('cost')).values('total')

    vehicles = Vehicle.objects.exclude(status=Vehicle.Status.RETIRED).annotate(
        total_fuel=Coalesce(Subquery(fuel_sq), Value(0, output_field=DecimalField()), output_field=DecimalField()),
        total_maintenance=Coalesce(Subquery(maint_sq), Value(0, output_field=DecimalField()), output_field=DecimalField()),
    )
    
    fuel_logs = FuelLog.objects.select_related('vehicle').all()

    context = {
        'expenses': expenses,
        'fuel_logs': fuel_logs,
        'completed_trips': completed_trips,
        'vehicle_costs': vehicles,
        'categories': Expense.Category.choices,
        'selected_category': category_filter,
    }
    return render(request, 'finance/expense_list.html', context)


@login_required
@role_required('manager', 'dispatcher')
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save()
            log_creation(expense, request.user, f'{expense.get_category_display()} expense: ₹{expense.cost}')
            if request.htmx:
                return _htmx_success_row(
                    request, 'finance/partials/expense_row.html', {'expense': expense},
                    'expense-table-body', f'Expense of ₹{expense.cost} logged.',
                )
            messages.success(request, f'Expense of ₹{expense.cost} logged successfully.')
            return redirect('finance:expense_list')
        else:
            if request.htmx:
                return _htmx_error_form(request, 'finance/partials/expense_modal_form.html',
                                        {'form': form, 'title': 'Log Expense', 'action_url': request.path})
    else:
        form = ExpenseForm()
    template = 'finance/partials/expense_modal_form.html' if request.htmx else 'finance/expense_form.html'
    return render(request, template, {'form': form, 'title': 'Log Expense', 'action_url': request.path})


@login_required
@role_required('manager', 'dispatcher')
def fuel_create(request):
    if request.method == 'POST':
        form = FuelLogForm(request.POST)
        if form.is_valid():
            log = form.save()
            log_creation(log, request.user, f'Fuel Log: {log.liters}L for ₹{log.cost}')
            if request.htmx:
                return _htmx_success_row(
                    request, 'finance/partials/fuel_row.html', {'log': log},
                    'fuel-table-body', f'Fuel log for {log.liters}L added.',
                )
            messages.success(request, f'Fuel log for {log.liters}L added.')
            return redirect('finance:expense_list')
        else:
            if request.htmx:
                return _htmx_error_form(request, 'finance/partials/fuel_modal_form.html',
                                        {'form': form, 'title': 'Log Fuel', 'action_url': request.path})
    else:
        form = FuelLogForm()
    template = 'finance/partials/fuel_modal_form.html' if request.htmx else 'finance/fuel_form.html'
    return render(request, template, {'form': form, 'title': 'Log Fuel', 'action_url': request.path})
