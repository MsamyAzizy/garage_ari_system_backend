# clients/admin.py

from django.contrib import admin
# Ensure you import Vehicle, assuming it's in the same models.py
from .models import Client, Vehicle 

class VehicleInline(admin.TabularInline):
    """Allows vehicles to be managed directly inside the Client admin page."""
    model = Vehicle
    extra = 1 # Number of empty forms to display

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
        ('Additional Notes', {
            'fields': ('notes',), 
            'classes': ('collapse',), 
        }),
    )

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('make', 'model', 'year', 'license_plate', 'client', 'odometer')
    search_fields = ('vin', 'license_plate', 'make', 'model')
    list_filter = ('make', 'year')