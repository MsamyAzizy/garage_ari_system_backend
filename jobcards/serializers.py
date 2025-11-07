# jobcards/serializers.py

from rest_framework import serializers
from .models import JobCard, LineItem, Payment
from clients.models import Client, Vehicle
from django.db import transaction

# ----------------------------------
# 1. Payment Serializer
# Handles nested payments within the JobCard
# ----------------------------------

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'payment_method', 'transaction_ref', 'date_paid']
        read_only_fields = ['id', 'date_paid']


# ----------------------------------
# 2. LineItem Serializer
# Handles nested parts and labor entries
# ----------------------------------

class LineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineItem
        fields = [
            'id', 'item_type', 'description', 'sku', 'quantity', 
            'unit_price', 'labor_time_hrs', 'line_total', 'date_added'
        ]
        read_only_fields = ['id', 'line_total', 'date_added']
        
    def validate(self, data):
        """
        Custom validation to ensure required fields are present based on item_type.
        """
        item_type = data.get('item_type')
        unit_price = data.get('unit_price')
        
        if item_type in ['PART', 'LABOR', 'FEE']:
            if unit_price is None or unit_price <= 0:
                raise serializers.ValidationError({"unit_price": "Price must be greater than zero for all line items."})
        
        return data


# ----------------------------------
# 3. Main JobCard Serializer (Handles Nested Create/Update)
# ----------------------------------

class JobCardSerializer(serializers.ModelSerializer):
    """
    Serializer for JobCard detail and CRUD. 
    Handles nested creation/updates of LineItems and Payments.
    """
    # Nested fields for the frontend form's tables
    line_items = LineItemSerializer(many=True, required=False)
    payments = PaymentSerializer(many=True, required=False, read_only=True)
    
    # Read-only fields for displaying related information in the list/detail view
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    vehicle_info = serializers.SerializerMethodField(read_only=True)
    technician_name = serializers.CharField(source='assigned_technician.username', read_only=True)
    
    # Custom property to expose the balance due
    balance_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = JobCard
        fields = [
            'id', 'job_number', 'status', 'date_in', 'date_promised', 'date_completed',
            'client', 'client_name', 'vehicle', 'vehicle_info', 'assigned_technician', 
            'technician_name', 'initial_odometer',
            'parts_subtotal', 'labor_subtotal', 'tax_amount', 
            'total_due', 'total_paid', 'balance_due',
            'line_items', 'payments' # Nested fields
        ]
        read_only_fields = [
            'id', 'job_number', 'date_in', 'total_due', 'total_paid', 'balance_due',
            'client_name', 'vehicle_info', 'technician_name'
        ]
        
    def get_vehicle_info(self, obj):
        """Helper to format vehicle string for list views."""
        return f"{obj.vehicle.year} {obj.vehicle.make} {obj.vehicle.model} ({obj.vehicle.license_plate or 'N/A'})"


    def create(self, validated_data):
        """
        Handle creation of JobCard and nested LineItems within a transaction.
        """
        # Separate nested data from the JobCard data
        line_items_data = validated_data.pop('line_items', [])
        
        with transaction.atomic():
            job_card = JobCard.objects.create(**validated_data)
            
            # Create nested LineItems
            for item_data in line_items_data:
                LineItem.objects.create(job_card=job_card, **item_data)
            
            # Recalculate and save totals (JobCard model method would handle this)
            job_card.recalculate_totals() # Assume this helper method exists on the JobCard model
            job_card.save() 
            
            return job_card

    def update(self, instance, validated_data):
        """
        Handle updates for JobCard and nested LineItems. 
        This is complex: we must determine which line items were added, removed, or changed.
        """
        line_items_data = validated_data.pop('line_items', [])
        
        # 1. Update the JobCard instance fields (status, dates, etc.)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        with transaction.atomic():
            instance.save()
            
            # 2. Handle Line Items
            # For simplicity, we'll implement a full replacement strategy here:
            # Delete all existing items and re-create them from the incoming data.
            # (A more advanced approach would diff the lists by ID).
            instance.line_items.all().delete()
            
            for item_data in line_items_data:
                LineItem.objects.create(job_card=instance, **item_data)
            
            # 3. Recalculate totals after updating line items
            instance.recalculate_totals() # Assume this helper method exists on the JobCard model
            instance.save() 
        
            return instance

# NOTE: Add a recalculate_totals() method to your JobCard model for clean updates.
# (This method should calculate parts_subtotal, labor_subtotal, tax_amount, and total_due)