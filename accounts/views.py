# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import StaffID

def role(request):
    return render(request, "accounts/role.html")


def doctor_login(request):
    if request.method == "POST":
        staff_id = request.POST.get("staff_id", "").strip()
        try:
            staff = StaffID.objects.get(staff_login_id=staff_id, role="doctor")
            request.session["staff_id"] = staff.staff_login_id
            request.session["role"] = staff.role
            return redirect("doctor_panel")  # name of your doctor dashboard url
        except StaffID.DoesNotExist:
            messages.error(request, "Invalid Doctor ID.")
    return render(request, "accounts/login-doctor.html")


def opd_login(request):
    if request.method == "POST":
        staff_id = request.POST.get("staff_id", "").strip()
        try:
            staff = StaffID.objects.get(staff_login_id=staff_id, role="reception")
            request.session["staff_id"] = staff.staff_login_id
            request.session["role"] = staff.role
            return redirect("opdpanel")
        except StaffID.DoesNotExist:
            messages.error(request, "Invalid Reception ID.")
    return render(request, "accounts/opd-login.html")


def pharmacy_login(request):
    if request.method == "POST":
        staff_id = request.POST.get("staff_id", "").strip()
        try:
            staff = StaffID.objects.get(staff_login_id=staff_id, role="pharmacy")
            request.session["staff_id"] = staff.staff_login_id
            request.session["role"] = staff.role
            return redirect("pharmacypanel")
        except StaffID.DoesNotExist:
            messages.error(request, "Invalid Pharmacy Code.")
    return render(request, "accounts/pharmacy-login.html")


def logout_staff(request):
    request.session.flush()
    return redirect("role")

from django.shortcuts import redirect
from functools import wraps

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            role = request.session.get("role")
            if role not in allowed_roles:
                return redirect("role")  # send back to role selection if not allowed
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
