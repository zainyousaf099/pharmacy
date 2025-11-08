from django.db import models
from django.contrib.auth.models import User
from opd.models import Patient
from inventory.models import Product
import uuid

# Create your models here.

class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions', null=True, blank=True)
    medicine = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='prescriptions')
    days = models.IntegerField(default=1, help_text='Number of days')
    morning = models.BooleanField(default=False, help_text='Take in morning')
    evening = models.BooleanField(default=False, help_text='Take in evening')
    night = models.BooleanField(default=False, help_text='Take at night')
    notes = models.TextField(blank=True, null=True, help_text='Additional instructions')
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        patient_name = self.patient.name if self.patient else 'Unknown'
        return f"{patient_name} - {self.medicine.name} ({self.days} days)"
