# clients/admin.py

from django.contrib import admin
# Ensure you import Vehicle, assuming it's in the same models.py
from .models import Client, Vehicle 

class VehicleInline(admin.TabularInline):
    """Allows vehicles to be managed directly inside the Client admin page."""
    model = Vehicle
    extra = 1 # Number of empty forms to display
    # 🛑 ADD: Include the new fields in the inline form
    fields = ('vin', 'license_plate', 'vehicle_type', 'year', 'make', 'model', 'odo_reading', 'odo_unit')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    # Display the new fields in the list view (if relevant) and search
    list_display = ('full_name', 'email', 'phone_number', 'client_type', 'date_created', 'is_active')
    # search_fields must include company_name now
    search_fields = ('first_name', 'last_name', 'company_name', 'email', 'phone_number', 'zip_code', 'tax_id') 
    list_filter = ('is_active', 'client_type', 'date_created') 
    inlines = [VehicleInline]

    # Organize the fields into collapsible sections in the detail view
    fieldsets = (
        ('Name & Type', { # 👈 Updated section title
            # 🛑 IMPORTANT: Include the new 'company_name' field here
            'fields': ('client_type', 'first_name', 'last_name', 'company_name', 'is_active') 
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number')
        }),
        ('Billing & Address', {
            'fields': ('address', 'city', 'state', 'zip_code', 'tax_id') 
        }),
        ('Client Settings', {
            'fields': (
                'is_tax_exempt', 'apply_discount',
                'labor_rate_override', 'custom_labor_rate',
                'parts_markup_override', 'custom_markup_percentage', 
                'payment_terms_override', 'custom_payment_terms'
            ),
            'classes': ('collapse',),
        }),
        ('Additional Notes', {
            'fields': ('notes',), 
            'classes': ('collapse',), 
        }),
    )

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    # 🛑 FIXED: Changed 'odometer' to 'odo_reading'
    list_display = ('make', 'model', 'year', 'license_plate', 'client', 'odo_reading', 'vehicle_type')
    
    # 🛑 ADDED: Include new fields in search
    search_fields = ('vin', 'license_plate', 'make', 'model', 'vehicle_type', 'color', 'unit_number')
    
    # 🛑 ADDED: More filter options
    list_filter = ('make', 'year', 'vehicle_type', 'odo_unit')
    
    # 🛑 ADDED: Organize fields in the detail view
    fieldsets = (
        ('Basic Information', {
            'fields': ('client', 'vin', 'license_plate', 'vehicle_type')
        }),
        ('Vehicle Specifications', {
            'fields': ('year', 'make', 'model', 'trim', 'color')
        }),
        ('Technical Details', {
            'fields': ('transmission', 'drivetrain', 'engine')
        }),
        ('Usage & Identification', {
            'fields': ('odo_reading', 'odo_unit', 'unit_number', 'last_service_date')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
    )
    
    # 🛑 ADDED: Auto-complete for client field (helps with performance)
    autocomplete_fields = ['client']