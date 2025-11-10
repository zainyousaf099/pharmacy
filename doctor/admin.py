from django.contrib import admin
from .models import Prescription, PrescriptionTemplate, PrescriptionTemplateMedicine

# Register your models here.

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'medicine', 'days', 'morning', 'evening', 'night', 'created_at']
    list_filter = ['created_at', 'morning', 'evening', 'night']
    search_fields = ['patient__name', 'patient__ref_no', 'medicine__name']
    readonly_fields = ['created_at']


class PrescriptionTemplateMedicineInline(admin.TabularInline):
    model = PrescriptionTemplateMedicine
    extra = 1
    fields = ['medicine', 'days', 'morning', 'evening', 'night', 'notes', 'order']


@admin.register(PrescriptionTemplate)
class PrescriptionTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PrescriptionTemplateMedicineInline]


@admin.register(PrescriptionTemplateMedicine)
class PrescriptionTemplateMedicineAdmin(admin.ModelAdmin):
    list_display = ['template', 'medicine', 'days', 'morning', 'evening', 'night', 'order']
    list_filter = ['template', 'morning', 'evening', 'night']
    search_fields = ['template__name', 'medicine__name']
