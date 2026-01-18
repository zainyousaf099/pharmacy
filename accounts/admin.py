# accounts/admin.py
from django.contrib import admin
from .models import StaffID


@admin.register(StaffID)
class StaffIDAdmin(admin.ModelAdmin):
    list_display = ("staff_login_id", "role", "password")
    list_filter = ("role",)
    search_fields = ("staff_login_id",)
    ordering = ("staff_login_id",)
    list_editable = ("password",)  # Allow editing password directly in list view
