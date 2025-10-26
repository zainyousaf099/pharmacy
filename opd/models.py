# reception/models.py
import uuid
from django.db import models, transaction
from django.utils import timezone
from accounts.models import StaffID

class Patient(models.Model):
   
    ref_no = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        help_text="Automatically generated reference number, e.g. PAT000001"
    )

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True, null=True)
    temperature = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="kg")
    height = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="cm")

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
