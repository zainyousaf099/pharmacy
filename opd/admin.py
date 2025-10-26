# reception/admin.py
from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('ref_no', 'name', 'phone', 'age', 'temperature', 'created_at')
    search_fields = ('ref_no', 'name', 'phone')
    list_filter = ('created_at',)
    readonly_fields = ('ref_no', 'created_at', 'updated_at')
    ordering = ('-created_at',)
