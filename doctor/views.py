from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from inventory.models import Product
from opd.models import Patient
from doctor.models import Prescription
import json

# Create your views here.
@csrf_exempt
def doctor_panel(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prescriptions_data = data.get('prescriptions', [])
            patient_ref_no = data.get('patient_ref_no')
            
            if not patient_ref_no:
                return JsonResponse({'success': False, 'error': 'Patient reference number is required'})
            
            # Get the patient
            try:
                patient = Patient.objects.get(ref_no=patient_ref_no)
            except Patient.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Patient not found'})
            
            # Save prescriptions
            for rx_data in prescriptions_data:
                medicine_id = rx_data.get('medicine_id')
                days = rx_data.get('days', 1)
                morning = rx_data.get('morning', False)
                evening = rx_data.get('evening', False)
                night = rx_data.get('night', False)
                
                if medicine_id:
                    try:
                        medicine = Product.objects.get(id=medicine_id)
                        Prescription.objects.create(
                            patient=patient,
                            medicine=medicine,
                            days=days,
                            morning=morning,
                            evening=evening,
                            night=night,
                            created_by=request.user if request.user.is_authenticated else None
                        )
                    except Product.DoesNotExist:
                        continue
            
            # Return success with print URL
            print_url = f'/doctor/print-prescription/{patient_ref_no}/'
            return JsonResponse({'success': True, 'print_url': print_url})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'doctortemp/dashboard.html')


def search_medicines_api(request):
    """API endpoint for medicine autocomplete search"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'results': []})
    
    # Search medicines by name - simple and direct
    medicines = Product.objects.filter(name__icontains=query)[:10]
    
    results = []
    for medicine in medicines:
        results.append({
            'id': str(medicine.id),
            'name': medicine.name,
            'category': medicine.category.name if medicine.category else '',
            'dosage': medicine.weight_or_quantity or '',
            'stock': medicine.total_items
        })
    
    return JsonResponse({'results': results})


def search_patient(request):
    """API endpoint for patient search"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'success': False, 'error': 'Search query is required'})
    
    # Try to find patient by ref_no first, then by name
    patient = None
    try:
        patient = Patient.objects.filter(ref_no__iexact=query).first()
        if not patient:
            patient = Patient.objects.filter(name__icontains=query).first()
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
    if patient:
        details = f"""Reference No: {patient.ref_no}
Name: {patient.name}
Phone: {patient.phone or 'N/A'}
Age: {patient.age or 'N/A'} years
Weight: {patient.weight or 'N/A'} kg
Height: {patient.height or 'N/A'} cm
Temperature: {patient.temperature or 'N/A'} °C
Registered: {patient.created_at.strftime('%d %b %Y, %I:%M %p') if patient.created_at else 'N/A'}"""
        
        return JsonResponse({
            'success': True,
            'patient': {
                'ref_no': patient.ref_no,
                'name': patient.name,
                'details': details
            }
        })
    else:
        return JsonResponse({'success': False, 'error': 'Patient not found'})


def print_prescription(request, patient_ref_no):
    """View for printing prescription"""
    patient = get_object_or_404(Patient, ref_no=patient_ref_no)
    
    # Get latest prescriptions for this patient (from today or latest)
    prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')[:20]
    
    context = {
        'patient': patient,
        'prescriptions': prescriptions,
        'date': timezone.now().strftime('%d %b %Y'),
        'time': timezone.now().strftime('%I:%M %p')
    }
    
    return render(request, 'doctortemp/print_prescription.html', context)
