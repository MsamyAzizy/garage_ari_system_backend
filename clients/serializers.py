from rest_framework import serializers
from .models import Client, Vehicle, DEFAULT_VAT_RATE, DEFAULT_DISCOUNT_RATE 
from django.core import validators 
from django.core.exceptions import ValidationError 
from django.utils.translation import gettext_lazy as _ 
import json # NEW: Used for safely parsing boolean/decimal strings from CSV

# 🛑 DJOSER/USER IMPORTS (Crucial for My Account Profile)
from djoser.serializers import UserSerializer
from django.contrib.auth import get_user_model

# Get the active User model (handles custom user models)
User = get_user_model() 

# ----------------------------------
# 0. User Serializer (For Djoser's /users/me/ endpoint)
# ----------------------------------

class CustomUserSerializer(UserSerializer):
    """
    Custom serializer for the User model, exposing first_name and last_name 
    for the "My Account Profile" page updates (used by Djoser's /users/me/ endpoint).
    """
    class Meta(UserSerializer.Meta):
        model = User
        # Expose the updatable fields required by the frontend
        fields = ('id', 'email', 'first_name', 'last_name') 
        # Ensure ID and Email are read-only (standard security practice)
        read_only_fields = ('id', 'email') 


# ----------------------------------
# 1. Vehicle Serializer (FIXED - VIN Uniqueness REMOVED)
# ----------------------------------

class VehicleSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    
    # 🛑 FIX: Make client field optional and read-only for nested routes
    client = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        required=False,  # Not required in request data for nested routes
        write_only=True  # Hide from response to avoid confusion
    )

    class Meta:
        model = Vehicle
        fields = [
            'id', 'client', 'client_name', 'vin', 'license_plate', 
            'vehicle_type', 'year', 'make', 'model', 'trim', 'transmission',
            'drivetrain', 'engine', 'odo_reading', 'odo_unit', 'color',
            'unit_number', 'notes', 'last_service_date'
        ]
        read_only_fields = ['id', 'client_name']

    def validate(self, data):
        """
        Custom validation for vehicle data - ALLOWS DUPLICATE VINs
        """
        vin = data.get('vin')
        
        # Only clean the VIN if provided, but DON'T check for duplicates
        if vin and vin.strip():
            # Clean the VIN by stripping whitespace
            clean_vin = vin.strip()
            
            # 🛑 CRITICAL FIX: REMOVED VIN uniqueness check
            # Vehicles can now have duplicate VINs
            # This allows saving vehicles even if VIN already exists
            
            # Update the data with cleaned VIN
            data['vin'] = clean_vin
        else:
            # If VIN is empty or just whitespace, set it to None
            data['vin'] = None

        return data

    def create(self, validated_data):
        """
        Handle vehicle creation for both nested and direct routes
        """
        request = self.context.get('request')
        
        # 🛑 FIX: For nested routes, client comes from URL
        if request and hasattr(request, 'kwargs') and 'client_pk' in request.kwargs:
            client_pk = request.kwargs['client_pk']
            try:
                client = Client.objects.get(pk=client_pk)
                validated_data['client'] = client
            except Client.DoesNotExist:
                raise serializers.ValidationError({'client': 'Client not found.'})
        # 🛑 FIX: For direct routes, ensure client is provided in request data
        elif 'client' not in validated_data:
            raise serializers.ValidationError({
                'client': 'Client is required. Provide client ID in request data for direct routes.'
            })

        return super().create(validated_data)


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
    phone_number = serializers.CharField(
        max_length=20, allow_blank=True, allow_null=True, required=False, 
        validators=Client._meta.get_field('phone_number').validators
    )
    tax_id = serializers.CharField(max_length=50, allow_blank=True, allow_null=True, required=False)
    notes = serializers.CharField(
        style={'base_template': 'textarea.html'}, 
        allow_blank=True, allow_null=True, required=False
    )
    
    # Email is REQUIRED by the front-end and should be required here
    email = serializers.EmailField(
        max_length=255, required=True, allow_null=False, allow_blank=False,  
    )

    # ----------------------------------------------------
    # NEW SETTINGS FIELDS ADDED
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
        instance_type = self.instance.client_type if self.instance else 'Individual'
        client_type = data.get('client_type', instance_type)
        
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
            
            if 'first_name' in data: data['first_name'] = first_name
            if 'last_name' in data: data['last_name'] = last_name

        elif client_type == 'Company':
            company_name = get_field_value('company_name').strip()

            if not company_name:
                raise serializers.ValidationError({"company_name": _("Company Name is required for a Company client.")})
            
            data['first_name'] = None
            data['last_name'] = None
            
            if 'company_name' in data: data['company_name'] = company_name

        # --- 2. Validation for Override Values ---
        if data.get('labor_rate_override') and data.get('custom_labor_rate') is None:
             raise serializers.ValidationError({'custom_labor_rate': _("A custom labor rate must be provided if the labor rate override is checked.")})
             
        if data.get('parts_markup_override') and data.get('custom_markup_percentage') is None:
             raise serializers.ValidationError({'custom_markup_percentage': _("A custom markup percentage must be provided if the parts markup override is checked.")})
             
        custom_terms = get_field_value('custom_payment_terms').strip()
        if data.get('payment_terms_override') and not custom_terms:
             raise serializers.ValidationError({'custom_payment_terms': _("Custom payment terms must be provided if the payment terms override is checked.")})
        
        if 'custom_payment_terms' in data:
            data['custom_payment_terms'] = custom_terms if custom_terms else None


        # --- 3. Final Model Validation ---
        try:
            instance_data = self.instance.__dict__.copy() if self.instance else {}
            
            temp_data = {}
            for k, v in data.items():
                if k in Client._meta.get_fields() or k in self.Meta.fields:
                    temp_data[k] = v

            instance_data.update(temp_data)
            
            model_fields = [f.name for f in Client._meta.get_fields()]
            model_data = {k: v for k, v in instance_data.items() if k in model_fields or k == 'pk'} 
            
            temp_instance = Client(**model_data)
            temp_instance.clean() 
            
            data['custom_labor_rate'] = temp_instance.custom_labor_rate
            data['custom_markup_percentage'] = temp_instance.custom_markup_percentage
            data['custom_payment_terms'] = temp_instance.custom_payment_terms
            
        except ValidationError as e:
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
            'id', 'full_name', 'email', 'phone_number', 'client_type', 
            'address', 'city', 'state', 'tax_id', 'notes', 'date_created'
        ]
        read_only_fields = ['id', 'full_name', 'date_created']
        
        
# ----------------------------------
# 4. Client Import Serializer (for Bulk Import)
# ----------------------------------

class ClientImportSerializer(serializers.ModelSerializer):
    """
    Minimal serializer used only for bulk CSV import. 
    It focuses on data cleaning and uniqueness checks.
    """
    
    email = serializers.EmailField(max_length=255, required=True, allow_null=False, allow_blank=False)
    
    class Meta:
        model = Client
        # Fields must exactly match the expected cleaned headers from the CSV
        fields = [
            'first_name', 'last_name', 'company_name', 'email', 
            'phone_number', 'client_type', 'address', 'city', 'state', 
            'zip_code', 'tax_id', 'notes', 
            'is_tax_exempt', 'apply_discount',
            'labor_rate_override', 'custom_labor_rate',
            'parts_markup_override', 'custom_markup_percentage',
            'payment_terms_override', 'custom_payment_terms',
        ]
        
    def validate(self, data):
        """Minimal validation for import: check for name, type, and uniqueness."""
        
        client_type = data.get('client_type', 'Individual')
        first_name = data.get('first_name') or ''
        last_name = data.get('last_name') or ''
        company_name = data.get('company_name') or ''
        
        # 1. Enforce naming rules based on type
        if client_type == 'Individual' and not (first_name.strip() or last_name.strip()):
            raise serializers.ValidationError({"client_type": _("Individual clients must have a First Name or Last Name.")})
        
        if client_type == 'Company' and not company_name.strip():
            raise serializers.ValidationError({"client_type": _("Company clients must have a Company Name.")})
            
        # 2. Check for existing client by email (uniqueness)
        if data.get('email') and Client.objects.filter(email=data['email']).exists():
             raise serializers.ValidationError({"email": _(f"Client with email '{data['email']}' already exists.")})
             
        # 3. Data Cleaning: Convert empty strings to None (for nullable fields) or False (for boolean fields)
        
        # Nullable string fields
        for key in ['first_name', 'last_name', 'company_name', 'phone_number', 'address', 'city', 'state', 'zip_code', 'tax_id', 'notes', 'custom_payment_terms']:
            if key in data and data[key] == '':
                data[key] = None
        
        # Boolean fields (Handle 'TRUE', 'True', '1', or empty/None)
        for key in ['is_tax_exempt', 'apply_discount', 'labor_rate_override', 'parts_markup_override', 'payment_terms_override']:
            if key in data:
                # Use json.loads to safely parse boolean strings (e.g., 'True'/'False')
                try:
                    # Clean the string value before parsing
                    value_str = str(data[key]).strip().lower()
                    
                    if value_str in ('true', '1'):
                        data[key] = True
                    elif value_str in ('false', '0', ''):
                        data[key] = False
                    else:
                        # Fallback for unexpected non-empty value
                        data[key] = bool(data[key])
                except Exception:
                    # Treat any parsing error or unexpected string as False
                    data[key] = False
            else:
                 data[key] = False # Default to False if field is missing in CSV
                 
        # Decimal fields (Convert empty strings to None)
        for key in ['custom_labor_rate', 'custom_markup_percentage']:
            if key in data and data[key] == '':
                data[key] = None

        return data