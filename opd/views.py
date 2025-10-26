# reception/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
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
                patient.save()

                # Generate QR Code
                qr = qrcode.QRCode(version=1, box_size=4, border=2)
                qr.add_data(patient.ref_no)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")

                buffer = BytesIO()
                img.save(buffer, format="PNG")
                qr_image = base64.b64encode(buffer.getvalue()).decode()

                context = {
                    "clinic_name": "Demo Clinic",
                    "patient": patient,
                    "qr_image": qr_image,
                }
                return render(request, "opdtemp/print_receipt.html", context)

    context = {
        "form": form,
        "selected_patient": selected_patient,
    }
    return render(request, "opdtemp/dashboard.html", context)





def patient_detail(request, ref_no):
    patient = get_object_or_404(Patient, ref_no=ref_no)
    return render(request, 'opdtemp/patient_detail.html', {'patient': patient})


def admit_patient(request):

    return render(request,'opdtemp/admit.html')