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
    batch_id = models.UUIDField(null=True, blank=True, help_text='Groups prescriptions issued together in one session')
    days = models.IntegerField(default=1, help_text='Number of days')
    morning = models.BooleanField(default=False, help_text='Take in morning')
    evening = models.BooleanField(default=False, help_text='Take in evening')
    night = models.BooleanField(default=False, help_text='Take at night')
    notes = models.TextField(blank=True, null=True, help_text='Additional instructions')
    is_dispensed = models.BooleanField(default=False, help_text='Whether this prescription has been dispensed to patient')
    dispensed_at = models.DateTimeField(null=True, blank=True, help_text='When the prescription was dispensed')
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        patient_name = self.patient.name if self.patient else 'Unknown'
        return f"{patient_name} - {self.medicine.name} ({self.days} days)"


# Prescription Template Models
class PrescriptionTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text='Template name (e.g., Headache, Stomach Pain)')
    description = models.TextField(blank=True, null=True, help_text='Brief description of when to use this template')
    presenting_complaints = models.TextField(blank=True, null=True, help_text='Presenting complaints section')
    development = models.TextField(blank=True, null=True, help_text='Development section')
    vaccination = models.TextField(blank=True, null=True, help_text='Vaccination section')
    medical_examination = models.TextField(blank=True, null=True, help_text='Medical examination findings section')
    investigation_advised = models.TextField(blank=True, null=True, help_text='Investigation advised section')
    provisional_diagnosis = models.TextField(blank=True, null=True, help_text='Provisional diagnosis section')
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class PrescriptionTemplateMedicine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(PrescriptionTemplate, on_delete=models.CASCADE, related_name='medicines')
    medicine = models.ForeignKey(Product, on_delete=models.CASCADE)
    days = models.IntegerField(default=1, help_text='Number of days')
    morning = models.BooleanField(default=False, help_text='Take in morning')
    evening = models.BooleanField(default=False, help_text='Take in evening')
    night = models.BooleanField(default=False, help_text='Take at night')
    notes = models.TextField(blank=True, null=True, help_text='Additional instructions')
    order = models.IntegerField(default=0, help_text='Display order')
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.template.name} - {self.medicine.name}"
