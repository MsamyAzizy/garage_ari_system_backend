# inventory/admin.py

from django.contrib import admin
from .models import InventoryPart, Category, Vendor

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_name', 'phone_number')
    search_fields = ('name',)

@admin.register(InventoryPart)
class InventoryPartAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'stock_qty', 'sale_price', 'is_active')
    search_fields = ('name', 'sku')
    list_filter = ('category', 'vendor', 'is_active')
    actions = ['increase_stock', 'decrease_stock']
    
    # Custom admin actions for inventory management
    @admin.action(description='Increase stock by 10')
    def increase_stock(self, request, queryset):
        for part in queryset:
            part.stock_qty += 10
            part.save()
        self.message_user(request, f"Successfully increased stock for {queryset.count()} parts.")