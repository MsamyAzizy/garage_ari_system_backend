# employees/models.py (UPDATED - Removed uniqueness for optional fields)

from django.db import models

class Employee(models.Model):
    # --- 1. BASIC INFORMATION ---
    employee_id = models.CharField(max_length=10, unique=True, verbose_name="Employee ID")
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, blank=True, null=True)
    dob = models.DateField(blank=True, null=True, verbose_name="Date of Birth")
    nationality = models.CharField(max_length=50, blank=True, null=True)
    marital_status = models.CharField(max_length=20, blank=True, null=True)
    
    # ✅ national_id: Removed unique=True
    national_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="National ID/Passport")
    
    # ✅ tin: Removed unique=True
    tin = models.CharField(max_length=50, blank=True, null=True, verbose_name="TIN")

    # --- 2. CONTACT DETAILS ---
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(unique=True) 
    residential_address = models.CharField(max_length=255, blank=True, null=True)
    postal_address = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    emergency_relationship = models.CharField(max_length=50, blank=True, null=True)

    # --- 3. JOB DETAILS ---
    job_title = models.CharField(max_length=100)
    department = models.CharField(max_length=50) 
    division = models.CharField(max_length=50, blank=True, null=True)
    employment_type = models.CharField(max_length=20) 
    employment_status = models.CharField(max_length=20, default='Active') 
    date_of_hire = models.DateField(verbose_name="Date of Hire")
    contract_start_date = models.DateField(blank=True, null=True)
    contract_end_date = models.DateField(blank=True, null=True)
    supervisor = models.CharField(max_length=100, blank=True, null=True)
    work_location = models.CharField(max_length=100, blank=True, null=True)
    grade = models.CharField(max_length=50, blank=True, null=True)
    
    # --- 4. SALARY & FINANCE ---
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    
    # ✅ bank_account_number: Removed unique=True
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    
    payment_method = models.CharField(max_length=50, default='Bank Transfer')
    currency = models.CharField(max_length=5, default='USD')
    nssf_number = models.CharField(max_length=50, blank=True, null=True)
    nhif_number = models.CharField(max_length=50, blank=True, null=True)

    # --- 5. EDUCATION & SKILLS ---
    highest_education = models.CharField(max_length=50, blank=True, null=True)
    institution_name = models.CharField(max_length=100, blank=True, null=True)
    field_of_study = models.CharField(max_length=100, blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)
    professional_certifications = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    languages = models.CharField(max_length=100, blank=True, null=True)

    # --- META / Django Defaults ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"
    
    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        ordering = ['last_name', 'first_name']