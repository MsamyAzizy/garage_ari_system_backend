# jobcards/models.py

from django.db import models
from django.conf import settings
from clients.models import Client, Vehicle
from django.db.models import Sum, Q # 🚀 ADDED Sum and Q for aggregation
from decimal import Decimal # 🚀 ADDED Decimal for precise calculations

# --- Tax Rate: Define this as a constant, used in recalculation ---
TAX_RATE = Decimal('0.15') # Example: 15% tax rate

class JobCard(models.Model):
    """
    The main job/work order for a vehicle.
    """
    # Status Choices for the Job Card Workflow
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('OPEN', 'Open/In Progress'),
        ('INSPECT', 'Inspection/Diagnosis'),
        ('PENDING_APPROVAL', 'Pending Client Approval'),
        ('CLOSED', 'Completed & Invoiced'),
        ('PAID', 'Paid'),
        ('CANCELED', 'Canceled'),
    ]

    # Relationships (Foreign Keys)
    client = models.ForeignKey(
        Client, 
        on_delete=models.PROTECT, 
        related_name='job_cards'
    )
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.PROTECT, 
        related_name='job_cards'
    )
    # The user who opened/created the job card
    assigned_technician = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        related_name='assigned_jobs', 
        null=True, 
        blank=True
    )

    # Job Details
    job_number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Dates
    date_in = models.DateTimeField(auto_now_add=True)
    date_promised = models.DateTimeField(null=True, blank=True)
    date_completed = models.DateTimeField(null=True, blank=True)
    
    # Odometer Reading at check-in
    initial_odometer = models.IntegerField(help_text="Odometer reading at job start")

    # Financial Summary (Calculated fields)
    parts_subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    labor_subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_due = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        ordering = ['-date_in']
        verbose_name = "Job Card"
        verbose_name_plural = "Job Cards"

    def __str__(self):
        return f"Job #{self.job_number} - {self.client.full_name}"

    def save(self, *args, **kwargs):
        """Auto-generate job number on creation if not set."""
        if not self.job_number:
            last_job = JobCard.objects.all().order_by('-id').first()
            new_id = (last_job.id if last_job else 0) + 1
            self.job_number = f'J{new_id:06d}' # e.g., J000001
        super().save(*args, **kwargs)
        
    @property
    def balance_due(self):
        return self.total_due - self.total_paid

    # 🚀 NEW CRITICAL METHOD FOR FINANCIAL INTEGRITY
    def recalculate_totals(self):
        """
        Aggregates LineItems and recalculates all financial summary fields.
        Must be called from serializer's create/update methods.
        """
        # 1. Aggregate LineItem totals by type
        totals = self.line_items.aggregate(
            parts=Sum('line_total', filter=Q(item_type='PART')),
            labor=Sum('line_total', filter=Q(item_type='LABOR')),
            fees=Sum('line_total', filter=Q(item_type='FEE'))
        )
        
        # Coalesce to 0.00 and combine labor/fees
        self.parts_subtotal = totals.get('parts') or Decimal('0.00')
        self.labor_subtotal = (totals.get('labor') or Decimal('0.00')) + (totals.get('fees') or Decimal('0.00'))

        # 2. Calculate Tax and Total Due
        subtotal = self.parts_subtotal + self.labor_subtotal
        self.tax_amount = subtotal * TAX_RATE
        self.total_due = subtotal + self.tax_amount
        
        # Note: total_paid is updated via the Payment model's save method, 
        # but we can optionally update it here for completeness:
        self.total_paid = self.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # NOTE: self.save() must be called externally by the view/serializer
        # to commit these changes to the database.


class LineItem(models.Model):
    # ... (existing code, no changes needed)
    """
    Represents a single part or labor entry on a Job Card.
    """
    TYPE_CHOICES = [
        ('PART', 'Part'),
        ('LABOR', 'Labor'),
        ('FEE', 'Fee/Miscellaneous'),
    ]
    
    job_card = models.ForeignKey(
        JobCard,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    
    item_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, blank=True, null=True) 
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2) 
    labor_time_hrs = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    line_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_added']
        
    def __str__(self):
        return f"{self.item_type} - {self.description}"
        
    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Payment(models.Model):
    # ... (existing code, no changes needed)
    """
    Records a payment made against a Job Card.
    """
    METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Credit/Debit Card'),
        ('TRANSFER', 'Bank Transfer'),
        ('OTHER', 'Other'),
    ]
    
    job_card = models.ForeignKey(
        JobCard,
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    date_paid = models.DateTimeField(auto_now_add=True)
    transaction_ref = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['date_paid']
        
    def __str__(self):
        return f"Payment of {self.amount} for Job #{self.job_card.job_number}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        if is_new:
            self.job_card.total_paid = self.job_card.payments.aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0.00')
            self.job_card.save()