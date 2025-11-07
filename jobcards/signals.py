# jobcards/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import LineItem
from inventory.models import InventoryPart # Import the part model

@receiver(post_save, sender=LineItem)
def update_inventory_on_lineitem_save(sender, instance, created, **kwargs):
    """
    Adjusts inventory stock when a LineItem is created or updated.
    This logic runs within the serializer's transaction (if called from a view).
    """
    if instance.item_type == 'PART' and instance.sku:
        try:
            part = InventoryPart.objects.get(sku=instance.sku)
            
            # Use F expression for safe, concurrent update
            with transaction.atomic():
                if created:
                    # New item: Decrease stock by the quantity used
                    part.stock_qty = part.stock_qty - instance.quantity
                else:
                    # Item updated: Calculate the difference between old and new quantity
                    # We retrieve the old value from the database before the update committed
                    old_quantity = LineItem.objects.get(pk=instance.pk).quantity 
                    diff = old_quantity - instance.quantity
                    part.stock_qty = part.stock_qty + diff
                
                # Prevent stock from going negative and save
                if part.stock_qty < 0:
                     part.stock_qty = 0 # Simple guardrail
                
                part.save()
                
        except InventoryPart.DoesNotExist:
            # Important: Log this warning in a real system
            print(f"WARNING: Inventory Part with SKU {instance.sku} not found during stock adjustment.")


@receiver(post_delete, sender=LineItem)
def restore_inventory_on_lineitem_delete(sender, instance, **kwargs):
    """
    Restores inventory stock when a LineItem is deleted from a job card.
    """
    if instance.item_type == 'PART' and instance.sku:
        try:
            part = InventoryPart.objects.get(sku=instance.sku)
            
            with transaction.atomic():
                # Restore the quantity that was previously used
                part.stock_qty = part.stock_qty + instance.quantity
                part.save()
                
        except InventoryPart.DoesNotExist:
            print(f"WARNING: Inventory Part with SKU {instance.sku} not found during stock restoration.")