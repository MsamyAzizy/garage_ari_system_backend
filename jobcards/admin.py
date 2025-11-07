# jobcards/admin.py

from django.contrib import admin
from .models import JobCard, LineItem, Payment

# 1. Define Inlines for nested models
class LineItemInline(admin.TabularInline):
    """Allows parts and labor to be managed directly within the Job Card."""
    model = LineItem
    extra = 1 # Number of empty forms to display
    # Display calculated fields but prevent manual editing
    readonly_fields = ('line_total', 'date_added')

class PaymentInline(admin.TabularInline):
    """Allows payments to be recorded directly within the Job Card."""
    model = Payment
    extra = 1
    readonly_fields = ('date_paid',)

# 2. Define the main JobCard Admin
@admin.register(JobCard)
class JobCardAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = (
        'job_number', 'client', 'vehicle', 'status', 
        'date_in', 'total_due', 'balance_due'
    )
    
    # Fields to display in the detailed form
    fieldsets = (
        ('Job Details', {
            'fields': (
                'job_number', ('client', 'vehicle'), 
                'assigned_technician', 'status', 'initial_odometer'
            )
        }),
        ('Dates', {
            'fields': ('date_in', 'date_promised', 'date_completed')
        }),
        ('Financial Summary (Read Only)', {
            'fields': (
                'parts_subtotal', 'labor_subtotal', 'tax_amount', 
                'total_due', 'total_paid', 'balance_due'
            ),
            'classes': ('collapse',), # Hide calculations by default
        }),
    )

    search_fields = (
        'job_number', 'client__first_name', 'client__last_name', 
        'vehicle__license_plate', 'vehicle__vin'
    )
    list_filter = ('status', 'assigned_technician')
    
    # Include the nested inlines
    inlines = [LineItemInline, PaymentInline]
    
    # Make financial summary fields read-only
    readonly_fields = (
        'job_number', 'date_in', 'parts_subtotal', 'labor_subtotal', 
        'tax_amount', 'total_due', 'total_paid', 'balance_due'
    )