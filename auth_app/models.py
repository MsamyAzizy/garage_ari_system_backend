# auth_app/models.py

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


# ====================================================================
# 1. Custom Manager for Email Authentication (CRITICAL FIX)
# ====================================================================
class CustomUserManager(BaseUserManager):
    """
    Manager that supports creating users and superusers using 'email' 
    as the unique identifier instead of 'username'.
    """
    def create_user(self, email, password=None, **extra_fields): 
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # Call the new create_user method
        return self.create_user(email, password, **extra_fields)


# ====================================================================
# 2. Custom User Model - FULLY UPDATED for HR/Employee Management
# ====================================================================

# 🏆 NEW CHOICES FOR ROLES (Crucial for system permissions)
ROLE_CHOICES = (
    ('owner', 'Owner / Administrator'),
    ('manager', 'Shop Manager'),
    ('service_advisor', 'Service Advisor'),
    ('mechanic', 'Technician / Mechanic'),
    ('customer', 'Customer Account (Non-Employee)'), # Default
)

# Using an explicit status list for clarity
EMPLOYMENT_STATUS_CHOICES = (
    ('active', 'Active'),
    ('on_leave', 'On Leave'),
    ('suspended', 'Suspended'),
    ('terminated', 'Terminated'),
)


class User(AbstractUser):
    """
    Custom User model extending Django's built-in AbstractUser.
    Includes all necessary fields for Authentication, Employee Profile, and HR.
    """
    
    # -----------------------------------------------------------
    # CORE AUTHENTICATION FIELDS
    # -----------------------------------------------------------
    username = None 
    email = models.EmailField(unique=True, blank=False, null=False)
    avatar = models.ImageField(
        upload_to='avatars/', 
        null=True, 
        blank=True,
        verbose_name='Profile Picture'
    )
    
    # -----------------------------------------------------------
    # BASIC & EMPLOYEE STATUS FIELDS
    # -----------------------------------------------------------
    employee_id = models.CharField(
        max_length=15, 
        unique=True, 
        null=True, 
        blank=True,
        verbose_name='System Employee ID'
    )
    is_employee = models.BooleanField(
        default=False,
        help_text='Designates whether the user is considered shop personnel.',
    )
    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='customer', 
        verbose_name='User Role'
    )
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=50, blank=True, null=True)
    marital_status = models.CharField(max_length=20, blank=True, null=True)
    national_id = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name='National ID/Passport'
    )
    tin_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='TIN')
    
    # -----------------------------------------------------------
    # CONTACT & EMERGENCY FIELDS
    # -----------------------------------------------------------
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    residential_address = models.TextField(blank=True, null=True)
    postal_address = models.TextField(blank=True, null=True)
    
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    emergency_relationship = models.CharField(max_length=50, blank=True, null=True)

    # -----------------------------------------------------------
    # JOB & CONTRACT DETAILS
    # -----------------------------------------------------------
    job_title = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=50, blank=True, null=True)
    division = models.CharField(max_length=50, blank=True, null=True)
    grade = models.CharField(max_length=50, blank=True, null=True)
    employment_type = models.CharField(max_length=20, blank=True, null=True)
    employment_status = models.CharField(
        max_length=20, 
        choices=EMPLOYMENT_STATUS_CHOICES,
        default='active',
        blank=True, 
        null=True
    )
    date_of_hire = models.DateField(blank=True, null=True)
    contract_start_date = models.DateField(blank=True, null=True)
    contract_end_date = models.DateField(blank=True, null=True)
    work_location = models.CharField(max_length=100, blank=True, null=True)
    
    # Linking to another User (the Supervisor)
    supervisor = models.ForeignKey(
        'self', # Links to the User model itself
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='supervisees'
    )

    # -----------------------------------------------------------
    # SALARY & FINANCE FIELDS
    # -----------------------------------------------------------
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=5, default='USD')
    
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    
    nssf_number = models.CharField(max_length=50, blank=True, null=True)
    nhif_number = models.CharField(max_length=50, blank=True, null=True)

    # -----------------------------------------------------------
    # EDUCATION & SKILLS
    # -----------------------------------------------------------
    highest_education = models.CharField(max_length=50, blank=True, null=True)
    institution_name = models.CharField(max_length=150, blank=True, null=True)
    field_of_study = models.CharField(max_length=100, blank=True, null=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    professional_certifications = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    languages = models.CharField(max_length=255, blank=True, null=True)

    # -----------------------------------------------------------
    # DJANGO CONFIGURATION
    # -----------------------------------------------------------
    objects = CustomUserManager() 
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'is_employee', 'role'] 
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='ari_user_set',
        blank=True,
        help_text=('The groups this user belongs to.'),
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='ari_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
    def __str__(self):
        return self.get_full_name() or self.email
        
    def get_full_name(self):
        """Returns the first_name plus the last_name, with a space in between."""
        return f'{self.first_name} {self.last_name}'.strip()