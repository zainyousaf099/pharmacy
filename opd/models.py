# reception/models.py
import uuid
from django.db import models, transaction
from django.utils import timezone
from accounts.models import StaffID

class Patient(models.Model):
    QUEUE_STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('with_doctor', 'With Doctor'),
        ('checked', 'Checked'),
        ('none', 'Not in Queue'),
    ]
    
    PHARMACY_QUEUE_STATUS_CHOICES = [
        ('waiting', 'Waiting for Medicine'),
        ('dispensing', 'Dispensing'),
        ('completed', 'Completed'),
        ('none', 'Not in Pharmacy Queue'),
    ]
   
    ref_no = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        help_text="Automatically generated reference number, e.g. PAT000001"
    )

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True, null=True)
    temperature = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    age_years = models.PositiveIntegerField(blank=True, null=True, help_text="Age in years")
    age_months = models.PositiveIntegerField(blank=True, null=True, help_text="Age in months (0-11)")
    age_days = models.PositiveIntegerField(blank=True, null=True, help_text="Age in days (0-30)")
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="kg")
    height = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="cm")
    
    @property
    def age(self):
        """Return formatted age string like '3y 4m 15d' or '6m' or '20d'"""
        parts = []
        if self.age_years:
            parts.append(f"{self.age_years}y")
        if self.age_months:
            parts.append(f"{self.age_months}m")
        if self.age_days:
            parts.append(f"{self.age_days}d")
        return " ".join(parts) if parts else None
    
    # Doctor Queue system fields
    queue_status = models.CharField(max_length=20, choices=QUEUE_STATUS_CHOICES, default='none')
    queue_number = models.PositiveIntegerField(null=True, blank=True)
    queued_at = models.DateTimeField(null=True, blank=True)
    
    # Pharmacy Queue system fields
    pharmacy_queue_status = models.CharField(max_length=20, choices=PHARMACY_QUEUE_STATUS_CHOICES, default='none')
    pharmacy_queue_number = models.PositiveIntegerField(null=True, blank=True)
    pharmacy_queued_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # optional: who registered this patient
    created_by = models.ForeignKey(
        StaffID, on_delete=models.SET_NULL, null=True, blank=True, related_name='patients_created'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"{self.ref_no or 'UNSAVED'} — {self.name}"

    def save(self, *args, **kwargs):

        is_new = self.pk is None
        super().save(*args, **kwargs) 
        if is_new and (not self.ref_no):
            self.ref_no = f"PAT{self.pk:06d}"
            Patient.objects.filter(pk=self.pk).update(ref_no=self.ref_no)
            self.refresh_from_db(fields=['ref_no'])
