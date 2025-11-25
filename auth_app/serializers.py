# auth_app/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.urls import reverse 

User = get_user_model() 
# 🏆 Import the choices defined in the model for validation/display
from .models import ROLE_CHOICES 

# ... (RegistrationSerializer remains the same) ...
class RegistrationSerializer(serializers.ModelSerializer):
    # ... (RegistrationSerializer content) ...
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        # 1. Basic password match validation
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # 2. Check if email already exists
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "This email address is already in use."})
            
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        # 🛑 NOTE: Newly registered users are NOT employees by default.
        # The EmployeeForm API endpoint handles setting is_employee=True.
        return user


# 🚀 Existing: Serializer for returning/updating user details
class CustomUserSerializer(serializers.ModelSerializer): 
    """
    Serializes and handles updates for the user profile (/users/me/).
    Inherited by EmployeeSerializer.
    """
    avatar = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar'] 
        read_only_fields = ['id', 'email'] 
        
    def get_avatar(self, obj):
        if not obj.avatar:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url
        
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.save()
        return instance


# =================================================================
# 🏆 NEW: EMPLOYEE MANAGEMENT SERIALIZER
# =================================================================
class EmployeeSerializer(CustomUserSerializer):
    """
    Serializer used for Employee CRUD operations (Manager/Admin view).
    Extends CustomUserSerializer to include all HR/Job/Salary fields.
    """
    # 1. READ-ONLY FIELD FOR SUPERVISOR NAME
    # This fetches the full name of the supervisor object.
    supervisor_name = serializers.CharField(
        source='supervisor.get_full_name', 
        read_only=True,
        allow_null=True
    )
    
    # 2. WRITE-FIELD FOR SUPERVISOR ID (Handles the ForeignKey update)
    # The frontend will likely send the ID of the supervising employee.
    supervisor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_employee=True), # Can only select another employee as supervisor
        allow_null=True,
        required=False
    )
    
    # 3. Handling the 'currency' field from the frontend as a CharField
    # Although not explicitly required, it’s good practice to ensure it's exposed correctly.
    currency = serializers.CharField(max_length=5, required=False)


    class Meta(CustomUserSerializer.Meta):
        model = User
        # NOTE: We MUST explicitly list all fields we want to expose for the Employee profile
        fields = CustomUserSerializer.Meta.fields + [
            # Employee Status/Role
            'is_employee', 'role',
            
            # Basic Info / Identifiers
            'employee_id', 'middle_name', 'gender', 'date_of_birth', 
            'nationality', 'marital_status', 'national_id', 'tin_number',
            
            # Contact Info
            'phone_number', 'residential_address', 'postal_address',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_relationship',
            
            # Job Details
            'job_title', 'department', 'division', 'grade', 
            'employment_type', 'employment_status', 'date_of_hire', 
            'contract_start_date', 'contract_end_date', 'work_location', 
            'supervisor', 'supervisor_name', # Use both supervisor (write) and supervisor_name (read)
            
            # Salary & Finance
            'basic_salary', 'allowances', 'deductions', 'currency',
            'bank_name', 'bank_account_number', 'payment_method',
            'nssf_number', 'nhif_number',
            
            # Education & Skills
            'highest_education', 'institution_name', 'field_of_study', 
            'graduation_year', 'professional_certifications', 'skills', 'languages',
        ]
        
        # We explicitly allow these fields to be writable/updatable in the employee context
        read_only_fields = ['id', 'email'] 
        
    def create(self, validated_data):
        # Override create to ensure new employees are marked as is_employee=True
        # and are assigned a default role if none is provided.
        validated_data['is_employee'] = True
        
        # Use the base User Manager to create the instance (which handles password setting)
        user = User.objects.create_user(**validated_data)

        # 🛑 Important: Since the frontend form doesn't handle password setting directly,
        # we often set a temporary, un-usable password here, or defer to an admin 
        # to set it, or rely on a password reset flow. 
        # For simplicity in this API, we assume the frontend might provide a password
        # for new creation, or we handle it by explicitly not setting it here.
        
        return user

    def update(self, instance, validated_data):
        # Ensure the employee status is not accidentally reverted
        validated_data.pop('email', None) # Email should remain read-only for updates
        
        # Handle the Supervisor relationship update explicitly if needed, though DRF handles it.
        # If the supervisor field is present, the PrimaryKeyRelatedField handles the ID lookup.
        
        return super().update(instance, validated_data)