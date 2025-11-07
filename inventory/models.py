# inventory/models.py

from django.db import models

# ----------------------------------
# 1. Category Model (e.g., 'Filter', 'Oil', 'Tire')
# ----------------------------------

class Category(models.Model):
    """
    Groups inventory items. Used to filter and organize the parts list.
    Note: Category names should be singular (e.g., 'Filter') based on past notes.
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

# ----------------------------------
# 2. Vendor Model (Supplier)
# ----------------------------------

class Vendor(models.Model):
    """
    Represents a supplier or vendor for inventory parts.
    """
    name = models.CharField(max_length=150, unique=True)
    contact_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=17, blank=True)
    email = models.EmailField(blank=True)
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

# ----------------------------------
# 3. InventoryPart Model (The actual stock item)
# ----------------------------------

class InventoryPart(models.Model):
    """
    Represents an item available for sale or use in a job card.
    Tracks pricing and stock levels.
    """
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit or Part Number")
    
    # Relationships
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, # If category is deleted, set to NULL (don't delete part)
        related_name='parts',
        null=True,
        blank=True
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL, # If vendor is deleted, set to NULL
        related_name='supplied_parts',
        null=True,
        blank=True
    )
    
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cost paid to vendor")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price charged to client")
    
    # Stock Tracking
    stock_qty = models.IntegerField(default=0, help_text="Current quantity on hand")
    critical_qty = models.IntegerField(default=5, help_text="Minimum quantity before reordering")
    
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Inventory Part"
        verbose_name_plural = "Inventory Parts"
        
    def __str__(self):
        return f"[{self.sku}] {self.name}"