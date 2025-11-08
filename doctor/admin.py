from django.contrib import admin
from .models import Prescription

# Register your models here.

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'medicine', 'days', 'morning', 'evening', 'night', 'created_at']
    list_filter = ['created_at', 'morning', 'evening', 'night']
    search_fields = ['patient__name', 'patient__ref_no', 'medicine__name']
    readonly_fields = ['created_at']
