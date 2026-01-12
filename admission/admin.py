from django.contrib import admin
from .models import Room, Bed, AdmittedPatient, MedicineCharge, OtherCharge

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'floor', 'daily_rate', 'is_active', 'available_beds')
    list_filter = ('room_type', 'is_active')
    search_fields = ('room_number',)

@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('bed_number', 'room', 'is_occupied')
    list_filter = ('is_occupied', 'room__room_type')
    search_fields = ('bed_number', 'room__room_number')

@admin.register(AdmittedPatient)
class AdmittedPatientAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'opd_patient', 'room', 'bed', 'status', 'admission_date', 'discharge_date')
    list_filter = ('status', 'admission_date', 'room__room_type')
    search_fields = ('admission_number', 'opd_patient__name', 'opd_patient__ref_no')
    readonly_fields = ('admission_number', 'created_at', 'updated_at')

@admin.register(MedicineCharge)
class MedicineChargeAdmin(admin.ModelAdmin):
    list_display = ('admitted_patient', 'medicine_name', 'quantity', 'unit_price', 'total_price', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('admitted_patient__admission_number', 'medicine_name')

@admin.register(OtherCharge)
class OtherChargeAdmin(admin.ModelAdmin):
    list_display = ('admitted_patient', 'description', 'amount', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('admitted_patient__admission_number', 'description')
