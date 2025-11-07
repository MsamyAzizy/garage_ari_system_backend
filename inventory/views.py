# inventory/views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import InventoryPart, Category, Vendor
from .serializers import InventoryPartSerializer, CategorySerializer, VendorSerializer

# ----------------------------------
# 1. InventoryPart ViewSet (Core Parts CRUD)
# ----------------------------------

class InventoryPartViewSet(viewsets.ModelViewSet):
    """
    Provides full CRUD for Inventory Parts. Supports searching and filtering.
    """
    queryset = InventoryPart.objects.filter(is_active=True).select_related('category', 'vendor')
    serializer_class = InventoryPartSerializer
    permission_classes = [IsAuthenticated]
    
    # Filters for the frontend list view
    filter_backends = [SearchFilter, OrderingFilter]
    
    # Search fields: allows searching by name, SKU, or related category/vendor name
    search_fields = ['name', 'sku', 'category__name', 'vendor__name']
    
    # Ordering fields: allows frontend sorting by these fields
    ordering_fields = ['name', 'sku', 'sale_price', 'stock_qty']
    
    def perform_destroy(self, instance):
        """
        Soft-delete: Mark part as inactive instead of deleting it to preserve history 
        on old job cards.
        """
        instance.is_active = False
        instance.save()


# ----------------------------------
# 2. Category ViewSet (Lookup Data)
# ----------------------------------

class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD for part categories. Used to populate dropdowns.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    # Simple search is useful for finding categories quickly
    search_fields = ['name']


# ----------------------------------
# 3. Vendor ViewSet (Lookup Data)
# ----------------------------------

class VendorViewSet(viewsets.ModelViewSet):
    """
    CRUD for vendors/suppliers. Used to populate dropdowns.
    """
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'email']