from django.db import models
from django.contrib.auth.models import User
from opd.models import Patient
from inventory.models import Product
import uuid

# Frequency choices for prescription dosage
FREQUENCY_CHOICES = [
    ('OD', 'OD - Once daily (روزانہ ایک بار)'),
    ('BD', 'BD - Twice daily (دن میں دو بار)'),
    ('TDS', 'TDS - Three times daily (دن میں تین بار)'),
    ('QID', 'QID - Four times daily (دن میں چار بار)'),
    ('HS', 'HS - At bedtime (سوتے وقت)'),
    ('QAM', 'QAM - Every morning (ہر صبح)'),
    ('QPM', 'QPM - Every evening (ہر شام)'),
    ('SOS', 'SOS - When required (ضرورت کے وقت)'),
    ('STAT', 'STAT - Immediately (فوراً)'),
    ('QOD', 'QOD - Alternate day (ایک دن چھوڑ کر)'),
    ('QW', 'QW - Once weekly (ہفتے میں ایک بار)'),
    ('Q6H', 'Q6H - Every 6 hours (ہر 6 گھنٹے)'),
    ('Q8H', 'Q8H - Every 8 hours (ہر 8 گھنٹے)'),
    ('AC', 'AC - Before meals (کھانے سے پہلے)'),
    ('PC', 'PC - After meals (کھانے کے بعد)'),
]

# Dosage form choices
DOSAGE_FORM_CHOICES = [
    ('MG', 'MG'),
    ('CC', 'CC'),
    ('ML', 'ML'),
    ('TABLETS', 'Tablets'),
    ('CAPSULES', 'Capsules'),
    ('DROPS', 'Drops'),
    ('TSP', 'Teaspoon'),
    ('TBSP', 'Tablespoon'),
    ('SACHET', 'Sachet'),
    ('PUFF', 'Puff'),
    ('UNIT', 'Unit'),
]

# Urdu descriptions for frequency
FREQUENCY_URDU = {
    'OD': 'روزانہ ایک بار',
    'BD': 'دن میں دو بار',
    'TDS': 'دن میں تین بار',
    'QID': 'دن میں چار بار',
    'HS': 'سوتے وقت',
    'QAM': 'ہر صبح',
    'QPM': 'ہر شام',
    'SOS': 'ضرورت کے وقت',
    'STAT': 'فوراً',
    'QOD': 'ایک دن چھوڑ کر',
    'QW': 'ہفتے میں ایک بار',
    'Q6H': 'ہر 6 گھنٹے',
    'Q8H': 'ہر 8 گھنٹے',
    'AC': 'کھانے سے پہلے',
    'PC': 'کھانے کے بعد',
}

# Create your models here.

class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions', null=True, blank=True)
    medicine = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='prescriptions')
    batch_id = models.UUIDField(null=True, blank=True, help_text='Groups prescriptions issued together in one session')
    qty = models.DecimalField(max_digits=8, decimal_places=2, default=1, help_text='Quantity (can be decimal like 2.5)')
    dosage_form = models.CharField(max_length=20, choices=DOSAGE_FORM_CHOICES, default='MG', help_text='Dosage form')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='OD', help_text='Dosage frequency')
    days = models.IntegerField(default=1, help_text='Number of days')
    morning = models.BooleanField(default=False, help_text='Take in morning')
    evening = models.BooleanField(default=False, help_text='Take in evening')
    night = models.BooleanField(default=False, help_text='Take at night')
    notes = models.TextField(blank=True, null=True, help_text='Additional instructions / Special note')
    
    # Clinical Notes - saved with prescription for reprint
    presenting_complaints = models.TextField(blank=True, null=True, help_text='Presenting complaints section')
    development = models.TextField(blank=True, null=True, help_text='Development section')
    vaccination = models.TextField(blank=True, null=True, help_text='Vaccination section')
    medical_examination = models.TextField(blank=True, null=True, help_text='Medical examination findings section')
    investigation_advised = models.TextField(blank=True, null=True, help_text='Investigation advised section')
    provisional_diagnosis = models.TextField(blank=True, null=True, help_text='Provisional diagnosis section')
    
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
    qty = models.DecimalField(max_digits=8, decimal_places=2, default=1, help_text='Quantity (can be decimal like 2.5)')
    dosage_form = models.CharField(max_length=20, choices=DOSAGE_FORM_CHOICES, default='MG', help_text='Dosage form')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='OD', help_text='Dosage frequency')
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
