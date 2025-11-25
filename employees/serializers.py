# employees/serializers.py (UPDATED - Removed uniqueness validation)

from rest_framework import serializers
from .models import Employee

class EmployeeSerializer(serializers.ModelSerializer):
    # 🏆 MAPPING FIELDS: (Same as before, only internal validation changes)
    
    # --- BASIC INFORMATION ---
    employeeId = serializers.CharField(source='employee_id', max_length=10, required=False, allow_blank=True) 
    firstName = serializers.CharField(source='first_name', max_length=100)
    middleName = serializers.CharField(source='middle_name', max_length=100, allow_blank=True, required=False)
    lastName = serializers.CharField(source='last_name', max_length=100)
    
    gender = serializers.CharField(max_length=10, required=False, allow_blank=True) 
    dob = serializers.DateField(required=False, allow_null=True) 
    nationality = serializers.CharField(max_length=50, required=False, allow_blank=True)
    maritalStatus = serializers.CharField(source='marital_status', max_length=20, required=False, allow_blank=True)
    
    nationalId = serializers.CharField(source='national_id', max_length=50, required=False, allow_blank=True)
    tin = serializers.CharField(max_length=50, required=False, allow_blank=True)

    # --- CONTACT DETAILS ---
    phoneNumber = serializers.CharField(source='phone_number', max_length=20)
    email = serializers.EmailField() 
    
    residentialAddress = serializers.CharField(source='residential_address', max_length=255, required=False, allow_blank=True)
    postalAddress = serializers.CharField(source='postal_address', max_length=255, required=False, allow_blank=True)
    emergencyContactName = serializers.CharField(source='emergency_contact_name', max_length=100, required=False, allow_blank=True)
    emergencyContactPhone = serializers.CharField(source='emergency_contact_phone', max_length=20, required=False, allow_blank=True)
    emergencyRelationship = serializers.CharField(source='emergency_relationship', max_length=50, required=False, allow_blank=True)

    # --- JOB DETAILS ---
    jobTitle = serializers.CharField(source='job_title', max_length=100)
    department = serializers.CharField(max_length=50) 
    division = serializers.CharField(max_length=50, required=False, allow_blank=True)
    employmentType = serializers.CharField(source='employment_type', max_length=20)
    employmentStatus = serializers.CharField(source='employment_status', max_length=20)
    dateOfHire = serializers.DateField(source='date_of_hire')
    contractStartDate = serializers.DateField(source='contract_start_date', required=False, allow_null=True)
    contractEndDate = serializers.DateField(source='contract_end_date', required=False, allow_null=True)
    
    supervisor = serializers.CharField(max_length=100, required=False, allow_blank=True)
    grade = serializers.CharField(max_length=50, required=False, allow_blank=True)

    workLocation = serializers.CharField(source='work_location', max_length=100, required=False, allow_blank=True)
    

    # --- SALARY & FINANCE ---
    basicSalary = serializers.DecimalField(source='basic_salary', max_digits=10, decimal_places=2, required=False, allow_null=True)
    allowances = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    deductions = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    bankName = serializers.CharField(source='bank_name', max_length=100, required=False, allow_blank=True)
    
    bankAccountNumber = serializers.CharField(source='bank_account_number', max_length=50, required=False, allow_blank=True)
    
    paymentMethod = serializers.CharField(source='payment_method', max_length=50)
    currency = serializers.CharField(max_length=5) 
    nssfNumber = serializers.CharField(source='nssf_number', max_length=50, required=False, allow_blank=True)
    nhifNumber = serializers.CharField(source='nhif_number', max_length=50, required=False, allow_blank=True)

    # --- EDUCATION & SKILLS ---
    highestEducation = serializers.CharField(source='highest_education', max_length=50, required=False, allow_blank=True)
    institutionName = serializers.CharField(source='institution_name', max_length=100, required=False, allow_blank=True)
    fieldOfStudy = serializers.CharField(source='field_of_study', max_length=100, required=False, allow_blank=True)
    graduationYear = serializers.IntegerField(source='graduation_year', required=False, allow_null=True)
    professionalCertifications = serializers.CharField(source='professional_certifications', required=False, allow_blank=True)
    skills = serializers.CharField(required=False, allow_blank=True) 
    languages = serializers.CharField(max_length=100, required=False, allow_blank=True)


    class Meta:
        model = Employee
        fields = (
            'id', 'employeeId', 'firstName', 'middleName', 'lastName', 'gender', 'dob',
            'nationality', 'maritalStatus', 'nationalId', 'tin', 'phoneNumber', 'email',
            'residentialAddress', 'postalAddress', 'emergencyContactName', 'emergencyContactPhone',
            'emergencyRelationship', 'jobTitle', 'department', 'division', 'employmentType',
            'employmentStatus', 'dateOfHire', 'contractStartDate', 'contractEndDate',
            'supervisor', 'workLocation', 'grade', 'basicSalary', 'allowances', 'deductions',
            'bankName', 'bankAccountNumber', 'paymentMethod', 'currency', 'nssfNumber',
            'nhifNumber', 'highestEducation', 'institutionName', 'fieldOfStudy',
            'graduationYear', 'professionalCertifications', 'skills', 'languages',
        )

    # ✅ Removed custom validate_nationalId, validate_tin, validate_bankAccountNumber

    # 🛑 CRITICAL FIX: Keep the global validation to convert empty strings to None 
    # for data consistency, even if the fields are no longer unique.
    def validate(self, data):
        """
        Forces empty string values for nullable fields to be None 
        to prevent errors when saving to DateField, DecimalField, and IntegerField.
        """
        
        # Fields that are null=True, blank=True in the model and receive empty strings from frontend
        # Including date/number fields that need to become None:
        nullable_fields = [
            'national_id', 'tin', 'bank_account_number', 
            'middle_name', 'marital_status', 
            'residential_address', 'postal_address',
            'contract_start_date', 'contract_end_date', 
            'basic_salary', 'allowances', 'deductions',
            'graduation_year', # integer field
            # ... add any other nullable fields that could be sent as ""
        ]
        
        for field_name in nullable_fields:
            value = data.get(field_name)
            
            # Check if value is None, or is an empty string/whitespace
            # Note: For dates/numbers, the serializer might already convert '' to None, 
            # but this check ensures strings fields are explicitly set to None.
            if isinstance(value, str) and value.strip() == "":
                data[field_name] = None
        
        return data