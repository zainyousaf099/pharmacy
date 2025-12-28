from django.db import models
from django.utils import timezone
from opd.models import Patient
from accounts.models import StaffID
from decimal import Decimal

class Room(models.Model):
    ROOM_TYPES = (
        ('general', 'General Ward'),
        ('private', 'Private Room'),
        ('icu', 'ICU'),
        ('emergency', 'Emergency'),
    )
    
    room_number = models.CharField(max_length=20, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='general')
    floor = models.CharField(max_length=10, blank=True, null=True)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.room_number} - {self.get_room_type_display()}"
    
    def available_beds(self):
        return self.beds.filter(is_occupied=False).count()


class Bed(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=10)
    is_occupied = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('room', 'bed_number')
    
    def __str__(self):
        return f"Bed {self.bed_number} in {self.room.room_number}"


class AdmittedPatient(models.Model):
    STATUS_CHOICES = (
        ('admitted', 'Admitted'),
        ('discharged', 'Discharged'),
    )
    
    opd_patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='admissions')
    admission_number = models.CharField(max_length=20, unique=True, blank=True)
    
    admission_date = models.DateTimeField(default=timezone.now)
    admission_reason = models.TextField()
    initial_diagnosis = models.TextField(blank=True)
    
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='admitted_patients')
    bed = models.ForeignKey(Bed, on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='admitted')
    
    discharge_date = models.DateTimeField(null=True, blank=True)
    discharge_summary = models.TextField(blank=True)
    
    admitted_by = models.ForeignKey(StaffID, on_delete=models.SET_NULL, null=True, blank=True, related_name='admitted_patients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-admission_date']
    
    def __str__(self):
        return f"{self.admission_number} - {self.opd_patient.name}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.admission_number:
            self.admission_number = f"ADM{self.pk:06d}"
            AdmittedPatient.objects.filter(pk=self.pk).update(admission_number=self.admission_number)
            self.refresh_from_db(fields=['admission_number'])
    
    def total_room_charges(self):
        if not self.room or not self.admission_date:
            return Decimal('0.00')
        
        end_date = self.discharge_date or timezone.now()
        days = (end_date - self.admission_date).days + 1  # Include admission day
        return self.room.daily_rate * days
    
    def total_medicine_charges(self):
        return sum(charge.total_price() for charge in self.medicine_charges.all())
    
    def total_other_charges(self):
        return sum(charge.amount for charge in self.other_charges.all())
    
    def grand_total(self):
        return self.total_room_charges() + self.total_medicine_charges() + self.total_other_charges()


class MedicineCharge(models.Model):
    admitted_patient = models.ForeignKey(AdmittedPatient, on_delete=models.CASCADE, related_name='medicine_charges')
    medicine_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    prescription_reference = models.CharField(max_length=100, blank=True)
    
    added_by = models.ForeignKey(StaffID, on_delete=models.SET_NULL, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    def total_price(self):
        return self.unit_price * self.quantity
    
    def __str__(self):
        return f"{self.medicine_name} x {self.quantity} - Rs. {self.total_price()}"


class OtherCharge(models.Model):
    admitted_patient = models.ForeignKey(AdmittedPatient, on_delete=models.CASCADE, related_name='other_charges')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    added_by = models.ForeignKey(StaffID, on_delete=models.SET_NULL, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.description} - Rs. {self.amount}"
