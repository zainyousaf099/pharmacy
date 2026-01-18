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


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def verify_menu_password(request):
    """Verify password for sidebar menu access"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    try:
        data = json.loads(request.body)
        password = data.get('password', '')
        role = data.get('role', '')  # 'doctor', 'reception', 'pharmacy'
        
        if not password or not role:
            return JsonResponse({'success': False, 'error': 'Password and role required'})
        
        # Check if any staff with this role has this password
        staff = StaffID.objects.filter(role=role, password=password).first()
        
        if staff:
            return JsonResponse({
                'success': True, 
                'message': 'Access granted',
                'staff_id': staff.staff_login_id
            })
        else:
            return JsonResponse({'success': False, 'error': 'Invalid password'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


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
