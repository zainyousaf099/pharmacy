# reception/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from accounts.views import role_required
from .forms import PatientForm
from accounts.models import StaffID
from .models import Patient
import qrcode
import base64
from io import BytesIO


@role_required(["reception"])
def opdpanel(request):
    form = PatientForm()
    selected_patient = None
    print_patient_id = None

    if request.method == "POST":
        # 🔎 If search button pressed
        if "search_patient" in request.POST:
            query = request.POST.get("search_query", "").strip()
            search_results = Patient.objects.filter(
                Q(ref_no__icontains=query) |
                Q(name__icontains=query) |
                Q(phone__icontains=query)
            )
            if search_results.exists():
                selected_patient = search_results.first()
                form = PatientForm(instance=selected_patient)

        else:  # ➕ Save or Update patient
            if request.POST.get("patient_id"):  # update existing
                patient = Patient.objects.get(id=request.POST.get("patient_id"))
                form = PatientForm(request.POST, instance=patient)
            else:  # create new
                form = PatientForm(request.POST)

            if form.is_valid():
                patient = form.save(commit=False)

                # set created_by to StaffID
                staff_id = request.session.get("staff_id")
                staff = StaffID.objects.filter(staff_login_id=staff_id).first()
                patient.created_by = staff
                
                # Add patient to queue
                today = timezone.now().date()
                # Get next queue number for today
                last_queue = Patient.objects.filter(
                    queued_at__date=today
                ).order_by('-queue_number').first()
                
                next_queue_number = (last_queue.queue_number or 0) + 1 if last_queue else 1
                
                patient.queue_status = 'waiting'
                patient.queue_number = next_queue_number
                patient.queued_at = timezone.now()
                
                patient.save()

                # Set print patient ID to trigger new window print
                print_patient_id = patient.id
                form = PatientForm()  # Reset form for new entry

    context = {
        "form": form,
        "selected_patient": selected_patient,
        "print_patient_id": print_patient_id,
    }
    return render(request, "opdtemp/dashboard.html", context)


@role_required(["reception"])
def print_patient_receipt(request, patient_id):
    """Separate view for printing patient receipt in new window"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Generate QR Code
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(patient.ref_no)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_image = base64.b64encode(buffer.getvalue()).decode()

    context = {
        "clinic_name": "ZOONA CHILD CARE CLINIC",
        "patient": patient,
        "qr_image": qr_image,
        "queue_number": patient.queue_number,
    }
    return render(request, "opdtemp/print_receipt.html", context)


def get_patients_list(request):
    """API endpoint to get list of all patients for Previous Patients feature"""
    try:
        # Get last 100 patients ordered by creation date (most recent first)
        patients = Patient.objects.all().order_by('-created_at')[:100]
        
        patients_data = []
        for patient in patients:
            patients_data.append({
                'id': patient.id,
                'ref_no': patient.ref_no,
                'name': patient.name,
                'phone': patient.phone,
                'age': patient.age,
                'temperature': str(patient.temperature) if patient.temperature else None,
                'weight': str(patient.weight) if patient.weight else None,
                'height': str(patient.height) if patient.height else None,
                'created_at': patient.created_at.strftime('%d %b %Y %H:%M'),
            })
        
        return JsonResponse({'success': True, 'patients': patients_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def patient_detail(request, ref_no):
    patient = get_object_or_404(Patient, ref_no=ref_no)
    return render(request, 'opdtemp/patient_detail.html', {'patient': patient})


def admit_patient(request):

    return render(request,'opdtemp/admit.html')