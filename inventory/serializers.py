# inventory/serializers.py

from rest_framework import serializers
from .models import Category, Vendor, InventoryPart

# ----------------------------------
# 1. Category Serializer
# Used primarily for populating a dropdown list in the Part Form
# ----------------------------------

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


# ----------------------------------
# 2. Vendor Serializer
# Used primarily for populating a dropdown list in the Part Form
# ----------------------------------

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'contact_name', 'phone_number', 'email']
        read_only_fields = ['id']


# ----------------------------------
# 3. Inventory Part Serializer
# Used for CRUD operations and the main Inventory List
# ----------------------------------

class InventoryPartSerializer(serializers.ModelSerializer):
    """
    Serializer for the InventoryPart model.
    It exposes the name of the related Category and Vendor for the list view.
    """
    # Read-only fields to display names instead of IDs in the list
    category_name = serializers.CharField(source='category.name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)

    class Meta:
        model = InventoryPart
        fields = [
            'id', 'name', 'sku', 
            'category', 'category_name',  # Expose both ID (for saving) and Name (for viewing)
            'vendor', 'vendor_name',      # Expose both ID (for saving) and Name (for viewing)
            'cost_price', 'sale_price', 
            'stock_qty', 'critical_qty', 
            'is_active', 'date_created'
        ]
        read_only_fields = ['id', 'category_name', 'vendor_name', 'date_created']