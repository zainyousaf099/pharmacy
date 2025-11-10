from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from inventory.models import Product
from opd.models import Patient
from doctor.models import Prescription, PrescriptionTemplate, PrescriptionTemplateMedicine
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


# Template Management Views
def template_list(request):
    """View to list all prescription templates"""
    templates = PrescriptionTemplate.objects.all().order_by('-created_at')
    context = {
        'templates': templates
    }
    return render(request, 'doctortemp/templates_list.html', context)


@csrf_exempt
def template_create(request):
    """View to create a new prescription template"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            description = data.get('description', '')
            medicines = data.get('medicines', [])
            
            if not name:
                return JsonResponse({'success': False, 'error': 'Template name is required'})
            
            # Create template
            template = PrescriptionTemplate.objects.create(
                name=name,
                description=description,
                created_by=request.user if request.user.is_authenticated else None
            )
            
            # Add medicines to template
            for idx, med_data in enumerate(medicines):
                medicine_id = med_data.get('medicine_id')
                if medicine_id:
                    try:
                        medicine = Product.objects.get(id=medicine_id)
                        PrescriptionTemplateMedicine.objects.create(
                            template=template,
                            medicine=medicine,
                            days=med_data.get('days', 1),
                            morning=med_data.get('morning', False),
                            evening=med_data.get('evening', False),
                            night=med_data.get('night', False),
                            notes=med_data.get('notes', ''),
                            order=idx + 1
                        )
                    except Product.DoesNotExist:
                        continue
            
            return JsonResponse({'success': True, 'template_id': str(template.id)})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'doctortemp/template_create.html')


def template_detail(request, template_id):
    """View to show template details"""
    template = get_object_or_404(PrescriptionTemplate, id=template_id)
    medicines = PrescriptionTemplateMedicine.objects.filter(template=template).order_by('order')
    
    context = {
        'template': template,
        'medicines': medicines
    }
    return render(request, 'doctortemp/template_detail.html', context)


@csrf_exempt
def template_delete(request, template_id):
    """View to delete a template"""
    if request.method == 'POST':
        try:
            template = get_object_or_404(PrescriptionTemplate, id=template_id)
            template.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_template_medicines_api(request, template_id):
    """API endpoint to get all medicines from a template"""
    try:
        template = get_object_or_404(PrescriptionTemplate, id=template_id)
        medicines = PrescriptionTemplateMedicine.objects.filter(template=template).order_by('order')
        
        results = []
        for med in medicines:
            results.append({
                'medicine_id': str(med.medicine.id),
                'medicine_name': med.medicine.name,
                'days': med.days,
                'morning': med.morning,
                'evening': med.evening,
                'night': med.night,
                'notes': med.notes,
                'category': med.medicine.category.name if med.medicine.category else '',
                'dosage': med.medicine.weight_or_quantity or '',
                'stock': med.medicine.total_items
            })
        
        return JsonResponse({'success': True, 'medicines': results})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_all_templates_api(request):
    """API endpoint to get all templates for dropdown"""
    try:
        templates = PrescriptionTemplate.objects.all().order_by('name')
        results = []
        for template in templates:
            medicine_count = PrescriptionTemplateMedicine.objects.filter(template=template).count()
            results.append({
                'id': str(template.id),
                'name': template.name,
                'description': template.description,
                'medicine_count': medicine_count
            })
        
        return JsonResponse({'success': True, 'templates': results})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

