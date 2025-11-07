# clients/serializers.py

from rest_framework import serializers
# Ensure the updated models.py is being used
from .models import Client, Vehicle, DEFAULT_VAT_RATE, DEFAULT_DISCOUNT_RATE 
from django.core import validators 
from django.core.exceptions import ValidationError 
from django.utils.translation import gettext_lazy as _ 

# ----------------------------------
# 1. Vehicle Serializer
# ----------------------------------

class VehicleSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.full_name', read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id', 'client', 'client_name', 'vin', 'license_plate', 
            'make', 'model', 'year', 'odometer', 'last_service_date'
        ]
        read_only_fields = ['id', 'client_name']


# ----------------------------------
# 2. Client Detail Serializer (Handles Conditional Validation and Settings)
# ----------------------------------

class ClientDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for the Client detail view, including all related vehicles and settings.
    Handles conditional validation for Individual vs. Company names.
    """
    vehicles = VehicleSerializer(many=True, read_only=True)
    
    # --- IDENTITY FIELDS (Must be optional/nullable) ---
    first_name = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)
    last_name = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)
    company_name = serializers.CharField(max_length=255, allow_blank=True, allow_null=True, required=False)
    
    # --- CONTACT & METADATA ---
    # Phone number uses validators defined in the model
    phone_number = serializers.CharField(
        max_length=20, 
        allow_blank=True,
        allow_null=True, 
        required=False, 
        validators=Client._meta.get_field('phone_number').validators
    )
    tax_id = serializers.CharField(max_length=50, allow_blank=True, allow_null=True, required=False)
    notes = serializers.CharField(
        style={'base_template': 'textarea.html'}, 
        allow_blank=True,
        allow_null=True, 
        required=False
    )
    
    # Email is REQUIRED by the front-end and should be required here
    email = serializers.EmailField(
        max_length=255, 
        required=True,      
        allow_null=False,   
        allow_blank=False,  
    )

    # ----------------------------------------------------
    # 🏆 NEW SETTINGS FIELDS ADDED
    # ----------------------------------------------------
    is_tax_exempt = serializers.BooleanField(required=False)
    apply_discount = serializers.BooleanField(required=False)
    
    labor_rate_override = serializers.BooleanField(required=False)
    custom_labor_rate = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True
    )
    
    parts_markup_override = serializers.BooleanField(required=False)
    custom_markup_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True
    )
    
    payment_terms_override = serializers.BooleanField(required=False)
    custom_payment_terms = serializers.CharField(
        max_length=50, required=False, allow_blank=True, allow_null=True
    )


    class Meta:
        model = Client
        
        fields = [
            'id', 'first_name', 'last_name', 'company_name', 'full_name', 'email', 
            'phone_number', 
            'client_type', 
            'address', 'city', 'state', 'zip_code', 
            'tax_id', 
            'notes',    
            'is_active', 'date_created', 'vehicles',
            # New Settings Fields:
            'is_tax_exempt', 'apply_discount',
            'labor_rate_override', 'custom_labor_rate',
            'parts_markup_override', 'custom_markup_percentage',
            'payment_terms_override', 'custom_payment_terms',
        ]
        read_only_fields = ['id', 'full_name', 'date_created']
        
        
    def validate(self, data):
        """
        Custom validation to enforce conditional required fields 
        based on the client_type, and checks override fields.
        """
        # Determine client type based on incoming data or existing instance
        instance_type = self.instance.client_type if self.instance else 'Individual'
        client_type = data.get('client_type', instance_type)
        
        # Helper to get field value, falling back to instance if not in data, then to empty string
        def get_field_value(field_name):
            value = data.get(field_name)
            if value is None and self.instance and hasattr(self.instance, field_name):
                value = getattr(self.instance, field_name)
            return value if value is not None else ''

        # --- 1. Validation and Data Cleansing for Names ---
        
        if client_type == 'Individual':
            first_name = get_field_value('first_name').strip()
            last_name = get_field_value('last_name').strip()

            if not first_name and not last_name:
                raise serializers.ValidationError({
                    'first_name': _("Must provide at least a First Name or a Last Name for an Individual client."),
                })
            
            data['company_name'] = None 
            
            # Only update data if the field was passed in the request or if it was cleared
            if 'first_name' in data: data['first_name'] = first_name
            if 'last_name' in data: data['last_name'] = last_name


        elif client_type == 'Company':
            company_name = get_field_value('company_name').strip()

            if not company_name:
                raise serializers.ValidationError({"company_name": _("Company Name is required for a Company client.")})
            
            data['first_name'] = None
            data['last_name'] = None
            
            if 'company_name' in data: data['company_name'] = company_name

        # --- 2. Validation for Override Values (Decimal/String presence) ---
        
        # Check if labor override is ON but value is missing
        if data.get('labor_rate_override') and data.get('custom_labor_rate') is None:
             raise serializers.ValidationError({
                 'custom_labor_rate': _("A custom labor rate must be provided if the labor rate override is checked."),
             })
             
        # Check if parts markup override is ON but value is missing
        if data.get('parts_markup_override') and data.get('custom_markup_percentage') is None:
             raise serializers.ValidationError({
                 'custom_markup_percentage': _("A custom markup percentage must be provided if the parts markup override is checked."),
             })
             
        # Check if payment terms override is ON but value is missing/empty
        custom_terms = get_field_value('custom_payment_terms').strip()
        if data.get('payment_terms_override') and not custom_terms:
             raise serializers.ValidationError({
                 'custom_payment_terms': _("Custom payment terms must be provided if the payment terms override is checked."),
             })
        
        # Clean the custom terms if provided
        if 'custom_payment_terms' in data:
            data['custom_payment_terms'] = custom_terms if custom_terms else None


        # --- 3. Final Model Validation (uses the model's clean() method) ---
        
        try:
            # Prepare data to call the model's clean() method
            instance_data = {}
            if self.instance:
                instance_data.update(self.instance.__dict__) 
            
            # Apply incoming data, ensuring only model fields are passed to the model
            temp_data = {}
            for k, v in data.items():
                if k in self.Meta.fields or k in Client._meta.get_fields():
                    temp_data[k] = v

            instance_data.update(temp_data)
            
            model_fields = [f.name for f in Client._meta.get_fields()]
            model_data = {k: v for k, v in instance_data.items() if k in model_fields or k == 'pk'} 
            
            temp_instance = Client(**model_data)
            
            # Runs model-level validation (like email uniqueness, required email check, and override cleanup)
            temp_instance.clean() 
            
            # Update data dictionary with cleaned values from the model's clean() method
            data['custom_labor_rate'] = temp_instance.custom_labor_rate
            data['custom_markup_percentage'] = temp_instance.custom_markup_percentage
            data['custom_payment_terms'] = temp_instance.custom_payment_terms
            
        except ValidationError as e:
            # Re-raise model validation errors as DRF errors
            raise serializers.ValidationError(e.message_dict)

        return data


# ----------------------------------
# 3. Client List Serializer (Simple)
# ----------------------------------

class ClientListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for the Client list view (for faster loading).
    """
    full_name = serializers.CharField(read_only=True) 

    class Meta:
        model = Client
        fields = [
            'id', 
            'full_name', 
            'email', 
            'phone_number', 
            'client_type', 
            'address',   
            'city',      
            'state',     
            'tax_id',    
            'notes',     
            'date_created'
            # Note: The new settings are intentionally left out of the list view for brevity/speed.
        ]
        read_only_fields = ['id', 'full_name', 'date_created']