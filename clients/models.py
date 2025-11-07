# clients/models.py

from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError 

# ----------------------------------------------------
# 🏆 GLOBAL CONSTANTS FOR BUSINESS LOGIC
# ----------------------------------------------------
# Define the standard tax rate for invoicing (18% VAT)
DEFAULT_VAT_RATE = 0.18  # Represented as a decimal

# Define the standard discount rate (used if 'apply_discount' is True)
DEFAULT_DISCOUNT_RATE = 0.05 # Example: 5% discount

class Client(models.Model):
    """
    Represents a customer in the ARI system.
    This model holds all contact and billing information.
    """
    
    CLIENT_TYPE_CHOICES = (
        ('Individual', 'Customer name'), 
        ('Company', 'Company name / Business name'),
    )

    # --- IDENTITY FIELDS ---
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    
    company_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="Company/Business Name"
    ) 
    
    client_type = models.CharField(
        max_length=20,
        choices=CLIENT_TYPE_CHOICES,
        default='Individual',
        verbose_name="Client Type"
    )
    
    # --- METADATA & CONTACT ---
    tax_id = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="Tax/VAT ID",
        help_text="Tax identification number (e.g., VAT, TIN, or Business ID)."
    )
    
    notes = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Client Notes",
        help_text="Any important notes, preferences, or history about the client."
    )
    
    email = models.EmailField(max_length=255, unique=True, blank=True, null=True)
    
    # NOTE: The phone_regex validation defined in the original code is complex.
    # It will remain as-is, but a simpler validator might be better in a real international app.
    phone_regex = RegexValidator(
        regex=r'^\+?\d{1,4}[1-9]\d{8}$',
        message="Phone number must be a valid international format. The local number part must be exactly 9 digits long and cannot start with zero."
    )
    
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=20, 
        blank=True, 
        null=True 
    )
    
    # --- ADDRESS ---
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    # ----------------------------------------------------
    # 🏆 NEW CLIENT SETTINGS FIELDS 🏆
    # ----------------------------------------------------
    
    # 1. Tax & Discount Settings
    is_tax_exempt = models.BooleanField(
        default=False, 
        verbose_name="Tax Exempt",
        help_text="If activated, no taxes (VAT) will be added to this client's invoices."
    )
    
    apply_discount = models.BooleanField(
        default=False, 
        verbose_name="Apply Default Discount",
        help_text=f"If checked, the default discount ({int(DEFAULT_DISCOUNT_RATE * 100)}%) is applied to invoices."
    )
    
    # 2. Labor Rate Override
    labor_rate_override = models.BooleanField(
        default=False, 
        verbose_name="Custom Labor Rate",
        help_text="Enables a specific labor rate override for this client."
    )

    custom_labor_rate = models.DecimalField(
        max_digits=8, # Increased to allow larger rates, e.g., 99999.99
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Override Labor Rate ($)",
    )
    
    # 3. Parts Markup Override
    parts_markup_override = models.BooleanField(
        default=False, 
        verbose_name="Custom Parts Markup",
        help_text="Enables a specific parts markup percentage override for this client."
    )

    custom_markup_percentage = models.DecimalField(
        max_digits=5, # Allows percentages up to 999.99%
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Override Markup (%)",
    )
    
    # 4. Payment Terms Override
    payment_terms_override = models.BooleanField(
        default=False, 
        verbose_name="Custom Payment Terms",
        help_text="Enables specific payment terms for this client's invoices."
    )
    
    custom_payment_terms = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        verbose_name="Override Terms (e.g., 'Net 45')",
    )

    # ----------------------------------
    # 🏆 CRITICAL MODEL VALIDATION ADDITION
    # ----------------------------------
    def clean(self):
        """
        Custom validation to ensure required fields based on client_type are present 
        AND cleans up unused name/override fields before saving.
        """
        from django.db.models import Q # Import needed for Q objects
        
        # A. Handle cleanup and validation based on client_type
        if self.client_type == 'Individual':
            # 1. Clear company name
            self.company_name = None 
            # 2. Validate Individual name presence
            if not self.first_name and not self.last_name:
                raise ValidationError(
                    {'first_name': "Individual clients must have at least a First Name or a Last Name."}
                )

        elif self.client_type == 'Company':
            # 1. Clear individual names
            self.first_name = None
            self.last_name = None
            # 2. Validate Company name presence
            if not self.company_name:
                raise ValidationError(
                    {'company_name': "Company clients must have a Company Name."}
                )

        # B. Clean up override values if the corresponding boolean is False
        if not self.labor_rate_override:
            self.custom_labor_rate = None
        
        if not self.parts_markup_override:
            self.custom_markup_percentage = None
            
        if not self.payment_terms_override:
            self.custom_payment_terms = None

        # C. Ensure that either first/last name or company name is NOT null. (Redundant but safe)
        if not self.first_name and not self.last_name and not self.company_name:
            raise ValidationError(
                "Client record must contain a valid name (First/Last or Company Name)."
            )
        
        # D. Validate unique email only if it is provided (standard Django model cleaning)
        if self.email:
            # Check for existing email case-insensitively, excluding the current client (for edits)
            if Client.objects.filter(Q(email__iexact=self.email) & ~Q(pk=self.pk)).exists():
                 raise ValidationError(
                        {'email': "A client with this email address already exists."}
                    )


    class Meta:
        ordering = ['date_created'] 
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        
    @property
    def full_name(self):
        """Returns the appropriate name based on client_type."""
        if self.client_type == 'Company' and self.company_name:
            return self.company_name
        # Fallback for Individual/other types
        return f"{self.first_name or ''} {self.last_name or ''}".strip()
        
    def __str__(self):
        return self.full_name


class Vehicle(models.Model):
    """
    Represents a specific vehicle owned by a Client.
    Linked to the Client via a ForeignKey relationship.
    """
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name='vehicles',
        verbose_name="Owner"
    )
    
    vin = models.CharField(max_length=17, unique=True, help_text="Vehicle Identification Number (17 chars)")
    license_plate = models.CharField(max_length=20, blank=True, unique=True, null=True)
    
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    
    odometer = models.IntegerField(default=0, help_text="Current mileage/kilometers")
    last_service_date = models.DateField(null=True, blank=True)
    
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['make', 'model']
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"
        
    def __str__(self):
        return f"{self.year} {self.make} {self.model} ({self.license_plate or 'No Plate'})"