from django.db import models
from django.utils import timezone
import uuid

# Create your models here.

class PharmacySale(models.Model):
    """
    Track pharmacy sales/bills for reference in returns
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill_number = models.CharField(max_length=50, unique=True)
    patient_ref_no = models.CharField(max_length=50, blank=True, null=True)
    patient_name = models.CharField(max_length=255, default='Walk-in Customer')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_direct_sale = models.BooleanField(default=False)
    sale_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-sale_date']
        verbose_name = 'Pharmacy Sale'
        verbose_name_plural = 'Pharmacy Sales'
    
    def __str__(self):
        return f"Bill #{self.bill_number} - {self.patient_name} - Rs.{self.final_amount}"
    
    @classmethod
    def generate_bill_number(cls):
        """Generate unique bill number like BILL-20260118-001"""
        today = timezone.now().strftime('%Y%m%d')
        prefix = f"BILL-{today}-"
        
        # Get count of bills today
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = cls.objects.filter(sale_date__gte=today_start).count() + 1
        
        return f"{prefix}{count:03d}"


class PharmacySaleItem(models.Model):
    """
    Individual items in a pharmacy sale
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(PharmacySale, on_delete=models.CASCADE, related_name='items')
    medicine_id = models.UUIDField(blank=True, null=True)  # Reference to Product
    medicine_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medicine_form = models.CharField(max_length=50, default='tablet')
    
    class Meta:
        verbose_name = 'Sale Item'
        verbose_name_plural = 'Sale Items'
    
    def __str__(self):
        return f"{self.medicine_name} x {self.quantity}"


class MedicineReturn(models.Model):
    """
    Track medicine returns from customers
    """
    RETURN_REASONS = [
        ('wrong_medicine', 'Wrong Medicine Given'),
        ('expired', 'Expired Medicine'),
        ('damaged', 'Damaged Package'),
        ('allergy', 'Patient Allergy'),
        ('doctor_changed', 'Doctor Changed Prescription'),
        ('extra', 'Extra Medicine (Not Needed)'),
        ('other', 'Other Reason'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    return_number = models.CharField(max_length=50, unique=True)
    
    # Link to original sale (optional - for returns with bill)
    original_sale = models.ForeignKey(PharmacySale, on_delete=models.SET_NULL, 
                                       blank=True, null=True, related_name='returns')
    original_bill_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Customer info
    customer_name = models.CharField(max_length=255, default='Walk-in Customer')
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Return details
    return_reason = models.CharField(max_length=50, choices=RETURN_REASONS, default='other')
    return_reason_detail = models.TextField(blank=True, null=True)
    
    # Totals
    total_refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Timestamps
    return_date = models.DateTimeField(auto_now_add=True)
    processed_by = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-return_date']
        verbose_name = 'Medicine Return'
        verbose_name_plural = 'Medicine Returns'
    
    def __str__(self):
        return f"Return #{self.return_number} - Rs.{self.total_refund_amount}"
    
    @classmethod
    def generate_return_number(cls):
        """Generate unique return number like RET-20260118-001"""
        today = timezone.now().strftime('%Y%m%d')
        prefix = f"RET-{today}-"
        
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = cls.objects.filter(return_date__gte=today_start).count() + 1
        
        return f"{prefix}{count:03d}"


class MedicineReturnItem(models.Model):
    """
    Individual medicines being returned
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    return_record = models.ForeignKey(MedicineReturn, on_delete=models.CASCADE, related_name='items')
    
    medicine_id = models.UUIDField(blank=True, null=True)  # Reference to Product
    medicine_name = models.CharField(max_length=255)
    quantity_returned = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medicine_form = models.CharField(max_length=50, default='tablet')
    
    # Whether stock was added back
    stock_restored = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Return Item'
        verbose_name_plural = 'Return Items'
    
    def __str__(self):
        return f"{self.medicine_name} x {self.quantity_returned} returned"
