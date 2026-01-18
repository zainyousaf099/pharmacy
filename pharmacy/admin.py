from django.contrib import admin
from .models import PharmacySale, PharmacySaleItem, MedicineReturn, MedicineReturnItem


class PharmacySaleItemInline(admin.TabularInline):
    model = PharmacySaleItem
    extra = 0
    readonly_fields = ['medicine_name', 'quantity', 'unit_price', 'total_price', 'medicine_form']


@admin.register(PharmacySale)
class PharmacySaleAdmin(admin.ModelAdmin):
    list_display = ['bill_number', 'patient_name', 'final_amount', 'is_direct_sale', 'sale_date']
    list_filter = ['is_direct_sale', 'sale_date']
    search_fields = ['bill_number', 'patient_name', 'patient_ref_no']
    date_hierarchy = 'sale_date'
    inlines = [PharmacySaleItemInline]
    readonly_fields = ['bill_number', 'patient_ref_no', 'patient_name', 'total_amount', 
                       'discount_amount', 'final_amount', 'is_direct_sale', 'sale_date']


class MedicineReturnItemInline(admin.TabularInline):
    model = MedicineReturnItem
    extra = 0
    readonly_fields = ['medicine_name', 'quantity_returned', 'unit_price', 'refund_amount', 'stock_restored']


@admin.register(MedicineReturn)
class MedicineReturnAdmin(admin.ModelAdmin):
    list_display = ['return_number', 'customer_name', 'return_reason', 'total_refund_amount', 'return_date']
    list_filter = ['return_reason', 'return_date']
    search_fields = ['return_number', 'customer_name', 'original_bill_number']
    date_hierarchy = 'return_date'
    inlines = [MedicineReturnItemInline]
    readonly_fields = ['return_number', 'original_sale', 'original_bill_number', 'customer_name',
                       'customer_phone', 'return_reason', 'return_reason_detail', 
                       'total_refund_amount', 'return_date', 'processed_by']
