from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from django.db import models
from inventory.models import Product
from opd.models import Patient
from doctor.models import Prescription, PrescriptionTemplate, PrescriptionTemplateMedicine
import json
import uuid

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
            
            # Generate a unique batch_id for this prescription session
            batch_id = uuid.uuid4()
            
            # Save prescriptions with the same batch_id
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
                            batch_id=batch_id,
                            days=days,
                            morning=morning,
                            evening=evening,
                            night=night,
                            created_by=request.user if request.user.is_authenticated else None
                        )
                    except Product.DoesNotExist:
                        continue
            
            # Add patient to pharmacy queue
            from django.utils import timezone
            today = timezone.now().date()
            
            # Only add to pharmacy queue if not already waiting
            if patient.pharmacy_queue_status != 'waiting':
                # Get next pharmacy queue number for today
                last_pharmacy_queue = Patient.objects.filter(
                    pharmacy_queued_at__date=today,
                    pharmacy_queue_number__isnull=False
                ).order_by('-pharmacy_queue_number').first()
                
                next_pharmacy_queue = (last_pharmacy_queue.pharmacy_queue_number or 0) + 1 if last_pharmacy_queue else 1
                
                patient.pharmacy_queue_status = 'waiting'
                patient.pharmacy_queue_number = next_pharmacy_queue
                patient.pharmacy_queued_at = timezone.now()
                patient.save()
            
            # Return success with print URL including batch_id
            print_url = f'/doctor/print-prescription/{patient_ref_no}/?batch_id={batch_id}'
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
Age: {patient.age or 'N/A'}
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
    
    # Get batch_id and template_id from query parameters
    batch_id = request.GET.get('batch_id')
    template_id = request.GET.get('template_id')
    
    if batch_id:
        # Show prescriptions from the specified batch
        try:
            prescriptions = Prescription.objects.filter(
                patient=patient, 
                batch_id=batch_id
            ).order_by('-created_at')
        except Exception:
            # If batch_id is invalid, get the latest batch
            prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')[:20]
    else:
        # Get the most recent batch_id for this patient
        latest_prescription = Prescription.objects.filter(patient=patient).order_by('-created_at').first()
        
        if latest_prescription and latest_prescription.batch_id:
            # Show only prescriptions from the latest batch
            prescriptions = Prescription.objects.filter(
                patient=patient,
                batch_id=latest_prescription.batch_id
            ).order_by('-created_at')
        else:
            # Fallback: show latest prescriptions (for backward compatibility with old data)
            prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')[:20]
    
    # Get template data if template_id is provided
    template = None
    if template_id:
        try:
            template = PrescriptionTemplate.objects.get(id=template_id)
        except PrescriptionTemplate.DoesNotExist:
            template = None
    
    context = {
        'patient': patient,
        'prescriptions': prescriptions,
        'template': template,
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
            presenting_complaints = data.get('presenting_complaints', '')
            development = data.get('development', '')
            vaccination = data.get('vaccination', '')
            medical_examination = data.get('medical_examination', '')
            investigation_advised = data.get('investigation_advised', '')
            provisional_diagnosis = data.get('provisional_diagnosis', '')
            medicines = data.get('medicines', [])
            
            if not name:
                return JsonResponse({'success': False, 'error': 'Template name is required'})
            
            # Create template
            template = PrescriptionTemplate.objects.create(
                name=name,
                description=description,
                presenting_complaints=presenting_complaints,
                development=development,
                vaccination=vaccination,
                medical_examination=medical_examination,
                investigation_advised=investigation_advised,
                provisional_diagnosis=provisional_diagnosis,
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
    all_medicines = Product.objects.all().order_by('name')
    
    context = {
        'template': template,
        'medicines': medicines,
        'all_medicines': all_medicines
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


@csrf_exempt
def template_add_medicine(request, template_id):
    """Add medicine to a template"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            template = get_object_or_404(PrescriptionTemplate, id=template_id)
            medicine = get_object_or_404(Product, id=data.get('medicine_id'))
            
            # Get the highest order number and increment
            max_order = PrescriptionTemplateMedicine.objects.filter(template=template).aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            
            # Create the template medicine
            PrescriptionTemplateMedicine.objects.create(
                template=template,
                medicine=medicine,
                days=data.get('days', 1),
                morning=data.get('morning', False),
                evening=data.get('evening', False),
                night=data.get('night', False),
                notes=data.get('notes', ''),
                order=max_order + 1
            )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def template_remove_medicine(request, template_id, medicine_id):
    """Remove medicine from a template"""
    if request.method == 'POST':
        try:
            template_medicine = get_object_or_404(
                PrescriptionTemplateMedicine,
                id=medicine_id,
                template_id=template_id
            )
            template_medicine.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def template_update_sections(request, template_id):
    """Update prescription sections of a template"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            template = get_object_or_404(PrescriptionTemplate, id=template_id)
            
            # Update all section fields
            template.presenting_complaints = data.get('presenting_complaints', '')
            template.development = data.get('development', '')
            template.vaccination = data.get('vaccination', '')
            template.medical_examination = data.get('medical_examination', '')
            template.investigation_advised = data.get('investigation_advised', '')
            template.provisional_diagnosis = data.get('provisional_diagnosis', '')
            
            template.save()
            
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


def get_patient_prescriptions_api(request):
    """API endpoint to get patient's prescriptions by ref_no"""
    try:
        ref_no = request.GET.get('ref_no', '').strip()
        
        if not ref_no:
            return JsonResponse({'success': False, 'error': 'Reference number required'})
        
        # Get patient
        patient = Patient.objects.filter(ref_no=ref_no).first()
        
        if not patient:
            return JsonResponse({'success': False, 'error': 'Patient not found'})
        
        # Get the latest prescription to find the most recent batch_id
        latest_prescription = Prescription.objects.filter(patient=patient).order_by('-created_at').first()
        
        if not latest_prescription:
            return JsonResponse({'success': False, 'error': 'No prescriptions found'})
        
        # Filter prescriptions by the latest batch_id and exclude already dispensed ones
        if latest_prescription.batch_id:
            prescriptions = Prescription.objects.filter(
                patient=patient,
                batch_id=latest_prescription.batch_id,
                is_dispensed=False  # Only show non-dispensed prescriptions
            ).select_related('medicine').order_by('-created_at')
        else:
            # Fallback for old prescriptions without batch_id
            prescriptions = Prescription.objects.filter(
                patient=patient,
                is_dispensed=False  # Only show non-dispensed prescriptions
            ).select_related('medicine').order_by('-created_at')
        
        results = []
        for presc in prescriptions:
            results.append({
                'id': str(presc.id),
                'medicine_id': str(presc.medicine.id),
                'medicine_name': presc.medicine.name,
                'days': presc.days,
                'morning': presc.morning,
                'evening': presc.evening,
                'night': presc.night,
                'notes': presc.notes or '',
                'sale_price': float(presc.medicine.sale_price_per_subitem or presc.medicine.purchase_price_per_subitem or 0),
                'stock': float(presc.medicine.total_items),
                'created_at': presc.created_at.strftime('%d %b %Y')
            })
        
        return JsonResponse({
            'success': True,
            'prescriptions': results,
            'patient_name': patient.name
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def patient_statistics(request):
    """View patient statistics page"""
    from datetime import datetime, timedelta
    from django.db.models import Count
    
    # Get today's data by default
    today = timezone.now().date()
    start_date = today
    end_date = today
    
    # Get prescriptions for today
    prescriptions = Prescription.objects.filter(
        created_at__date=today
    ).select_related('patient').order_by('-created_at')
    
    # Group by patient and count prescriptions
    patients_data = {}
    for presc in prescriptions:
        if presc.patient:
            key = presc.patient.ref_no
            if key not in patients_data:
                patients_data[key] = {
                    'patient_name': presc.patient.name,
                    'ref_no': presc.patient.ref_no,
                    'phone': presc.patient.phone,
                    'date': presc.created_at.strftime('%d %b %Y'),
                    'prescription_count': 0
                }
            patients_data[key]['prescription_count'] += 1
    
    patients_list = list(patients_data.values())
    
    context = {
        'total_patients': len(patients_list),
        'total_prescriptions': prescriptions.count(),
        'avg_per_day': round(prescriptions.count() / max(1, len(patients_list)), 1) if patients_list else 0,
        'patients': patients_list,
    }
    
    return render(request, 'doctortemp/patient_stats.html', context)


def patient_statistics_api(request):
    """API endpoint for patient statistics"""
    from datetime import datetime, timedelta
    from django.db.models import Count
    
    try:
        filter_type = request.GET.get('filter', 'today')
        today = timezone.now().date()
        
        # Determine date range based on filter
        if filter_type == 'today':
            start_date = today
            end_date = today
        elif filter_type == 'week':
            start_date = today - timedelta(days=today.weekday())  # Start of week (Monday)
            end_date = today
        elif filter_type == 'month':
            start_date = today.replace(day=1)
            end_date = today
        elif filter_type == 'year':
            start_date = today.replace(month=1, day=1)
            end_date = today
        elif filter_type == 'custom':
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
        else:
            start_date = today
            end_date = today
        
        # Get prescriptions in date range
        prescriptions = Prescription.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('patient').order_by('-created_at')
        
        # Group by patient and count prescriptions
        patients_data = {}
        for presc in prescriptions:
            if presc.patient:
                key = presc.patient.ref_no
                if key not in patients_data:
                    patients_data[key] = {
                        'patient_name': presc.patient.name,
                        'ref_no': presc.patient.ref_no,
                        'phone': presc.patient.phone or '',
                        'date': presc.created_at.strftime('%d %b %Y'),
                        'prescription_count': 0
                    }
                patients_data[key]['prescription_count'] += 1
        
        patients_list = list(patients_data.values())
        
        # Calculate days in range
        days_count = (end_date - start_date).days + 1
        
        return JsonResponse({
            'success': True,
            'total_patients': len(patients_list),
            'total_prescriptions': prescriptions.count(),
            'avg_per_day': round(prescriptions.count() / max(1, days_count), 1),
            'patients': patients_list,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============ PATIENT QUEUE SYSTEM ============

def get_patient_queue(request):
    """Get all patients waiting in queue"""
    try:
        # Get patients with waiting or with_doctor status from today
        today = timezone.now().date()
        waiting_patients = Patient.objects.filter(
            queue_status__in=['waiting', 'with_doctor'],
            queued_at__date=today
        ).order_by('queue_number')
        
        queue_data = []
        for patient in waiting_patients:
            queue_data.append({
                'id': patient.id,
                'ref_no': patient.ref_no,
                'name': patient.name,
                'phone': patient.phone or '',
                'age': patient.age or '',
                'temperature': str(patient.temperature) if patient.temperature else '',
                'weight': str(patient.weight) if patient.weight else '',
                'queue_number': patient.queue_number,
                'status': patient.queue_status,
                'queued_at': patient.queued_at.strftime('%H:%M') if patient.queued_at else '',
            })
        
        return JsonResponse({
            'success': True,
            'queue': queue_data,
            'total_waiting': len([p for p in queue_data if p['status'] == 'waiting']),
            'total_with_doctor': len([p for p in queue_data if p['status'] == 'with_doctor']),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def select_patient_from_queue(request):
    """Select a patient from queue to check"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        data = json.loads(request.body)
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return JsonResponse({'success': False, 'error': 'Patient ID required'})
        
        patient = Patient.objects.get(id=patient_id)
        
        # Update status to with_doctor
        patient.queue_status = 'with_doctor'
        patient.save()
        
        return JsonResponse({
            'success': True,
            'patient': {
                'id': patient.id,
                'ref_no': patient.ref_no,
                'name': patient.name,
                'phone': patient.phone or '',
                'age': patient.age or '',
                'temperature': str(patient.temperature) if patient.temperature else '',
                'weight': str(patient.weight) if patient.weight else '',
                'height': str(patient.height) if patient.height else '',
            }
        })
    except Patient.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt  
def mark_patient_checked(request):
    """Mark patient as checked after prescription is saved"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        data = json.loads(request.body)
        patient_ref_no = data.get('patient_ref_no')
        
        if not patient_ref_no:
            return JsonResponse({'success': False, 'error': 'Patient reference number required'})
        
        patient = Patient.objects.get(ref_no=patient_ref_no)
        
        # Mark as checked
        patient.queue_status = 'checked'
        patient.save()
        
        return JsonResponse({'success': True, 'message': 'Patient marked as checked'})
    except Patient.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
