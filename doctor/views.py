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
            
            # Get clinical notes from the request
            clinical_notes = data.get('clinical_notes', {})
            presenting_complaints = clinical_notes.get('pc', '')
            development = clinical_notes.get('dev', '')
            vaccination = clinical_notes.get('vac', '')
            medical_examination = clinical_notes.get('me', '')
            investigation_advised = clinical_notes.get('ia', '')
            provisional_diagnosis = clinical_notes.get('pd', '')
            special_note = data.get('special_note', '')
            
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
                qty = rx_data.get('qty', 1)
                dosage_form = rx_data.get('dosage_form', 'MG')
                frequency = rx_data.get('frequency', 'OD')
                days = rx_data.get('days', 1)
                
                if medicine_id:
                    try:
                        medicine = Product.objects.get(id=medicine_id)
                        Prescription.objects.create(
                            patient=patient,
                            medicine=medicine,
                            batch_id=batch_id,
                            qty=qty,
                            dosage_form=dosage_form,
                            frequency=frequency,
                            days=days,
                            presenting_complaints=presenting_complaints,
                            development=development,
                            vaccination=vaccination,
                            medical_examination=medical_examination,
                            investigation_advised=investigation_advised,
                            provisional_diagnosis=provisional_diagnosis,
                            notes=special_note,
                            created_by=request.user if request.user.is_authenticated else None
                        )
                    except Product.DoesNotExist:
                        continue
            
            # Add patient to pharmacy queue
            from django.utils import timezone
            today = timezone.localtime(timezone.now()).date()
            
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
            'medicine_form': medicine.medicine_form or 'tablet',
            'stock': medicine.total_items
        })
    
    return JsonResponse({'results': results})


def search_patient(request):
    """API endpoint for patient search - supports ref_no, name, and phone"""
    query = request.GET.get('q', '').strip()
    patient_id = request.GET.get('id', '').strip()  # For selecting specific patient from results
    
    if not query and not patient_id:
        return JsonResponse({'success': False, 'error': 'Search query is required'})
    
    patient = None
    multiple_results = []
    
    try:
        # If specific patient ID is provided, get that patient directly
        if patient_id:
            patient = Patient.objects.filter(id=patient_id).first()
        else:
            # Try to find patient by ref_no first (exact match)
            patient = Patient.objects.filter(ref_no__iexact=query).first()
            
            if not patient:
                # Search by name or phone - may return multiple results
                from django.db.models import Q
                matching_patients = Patient.objects.filter(
                    Q(name__icontains=query) | Q(phone__icontains=query)
                ).order_by('-created_at')[:20]
                
                if matching_patients.count() == 1:
                    # Only one match, use it directly
                    patient = matching_patients.first()
                elif matching_patients.count() > 1:
                    # Multiple matches, return list for user to choose
                    for p in matching_patients:
                        multiple_results.append({
                            'id': str(p.id),
                            'ref_no': p.ref_no,
                            'name': p.name,
                            'phone': p.phone or 'N/A',
                            'age': p.age or 'N/A',
                            'registered': p.created_at.strftime('%d %b %Y') if p.created_at else 'N/A',
                            'initials': ''.join([n[0].upper() for n in p.name.split()[:2]]) if p.name else 'P'
                        })
                    return JsonResponse({
                        'success': True,
                        'multiple_results': True,
                        'patients': multiple_results,
                        'count': len(multiple_results)
                    })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
    if patient:
        # Find ALL patients with the same name OR phone number to combine their history
        # This handles cases where the same person was registered multiple times
        from django.db.models import Q
        related_patients = Patient.objects.filter(
            Q(name__iexact=patient.name) | 
            (Q(phone=patient.phone) & ~Q(phone='') & ~Q(phone__isnull=True))
        ).values_list('id', flat=True)
        
        # Get prescription history from ALL related patients, grouped by batch_id
        prescriptions = Prescription.objects.filter(
            patient_id__in=related_patients
        ).select_related('medicine', 'patient').order_by('-created_at')
        
        # Group by batch_id
        visits = {}
        for p in prescriptions:
            batch_key = str(p.batch_id) if p.batch_id else p.created_at.strftime('%Y%m%d%H%M%S')
            if batch_key not in visits:
                visits[batch_key] = {
                    'batch_id': str(p.batch_id) if p.batch_id else None,
                    'date': p.created_at.strftime('%d %b %Y, %I:%M %p'),
                    'patient_ref': p.patient.ref_no,  # Show which PAT number this was under
                    'medicines': []
                }
            visits[batch_key]['medicines'].append({
                'name': p.medicine.name if p.medicine else 'Unknown',
                'qty': float(p.qty) if p.qty else 1,
                'dosage_form': p.dosage_form,
                'frequency': p.frequency,
                'days': p.days,
                'morning': p.morning,
                'evening': p.evening,
                'night': p.night
            })
        
        # Convert to list and limit to last 10 visits
        visit_list = list(visits.values())[:10]
        
        # Count unique related patients for info
        related_count = len(set(related_patients))
        
        # Return structured data for better UI
        return JsonResponse({
            'success': True,
            'patient': {
                'ref_no': patient.ref_no,
                'name': patient.name,
                'phone': patient.phone or 'N/A',
                'age': patient.age or 'N/A',
                'weight': f"{patient.weight} kg" if patient.weight else 'N/A',
                'height': f"{patient.height} cm" if patient.height else 'N/A',
                'temperature': f"{patient.temperature} °C" if patient.temperature else 'N/A',
                'registered': patient.created_at.strftime('%d %b %Y, %I:%M %p') if patient.created_at else 'N/A',
                'initials': ''.join([n[0].upper() for n in patient.name.split()[:2]]) if patient.name else 'P'
            },
            'prescription_history': visit_list,
            'total_visits': len(visits),
            'related_patients_count': related_count  # How many PAT records found for this person
        })
    else:
        return JsonResponse({'success': False, 'error': 'Patient not found'})


def print_prescription(request, patient_ref_no):
    """View for printing prescription"""
    patient = get_object_or_404(Patient, ref_no=patient_ref_no)
    
    # Get batch_id and template_id from query parameters
    batch_id = request.GET.get('batch_id')
    template_id = request.GET.get('template_id')
    
    # Get clinical notes from query parameters (for direct input from dashboard)
    # Use simple keys for Django template compatibility
    pc = request.GET.get('pc', '')
    dev = request.GET.get('dev', '')
    vac = request.GET.get('vac', '')
    me = request.GET.get('me', '')
    ia = request.GET.get('ia', '')
    pd = request.GET.get('pd', '')
    special_note = request.GET.get('special_note', '')
    
    if batch_id:
        # Show prescriptions from the specified batch
        try:
            prescriptions = Prescription.objects.filter(
                patient=patient, 
                batch_id=batch_id
            ).order_by('-created_at')
            
            # If reprinting and no clinical notes in URL, get them from the saved prescription
            if prescriptions.exists():
                first_rx = prescriptions.first()
                if not pc and first_rx.presenting_complaints:
                    pc = first_rx.presenting_complaints
                if not dev and first_rx.development:
                    dev = first_rx.development
                if not vac and first_rx.vaccination:
                    vac = first_rx.vaccination
                if not me and first_rx.medical_examination:
                    me = first_rx.medical_examination
                if not ia and first_rx.investigation_advised:
                    ia = first_rx.investigation_advised
                if not pd and first_rx.provisional_diagnosis:
                    pd = first_rx.provisional_diagnosis
                if not special_note and first_rx.notes:
                    special_note = first_rx.notes
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
            
            # Get clinical notes from saved prescription if not in URL
            if not pc and latest_prescription.presenting_complaints:
                pc = latest_prescription.presenting_complaints
            if not dev and latest_prescription.development:
                dev = latest_prescription.development
            if not vac and latest_prescription.vaccination:
                vac = latest_prescription.vaccination
            if not me and latest_prescription.medical_examination:
                me = latest_prescription.medical_examination
            if not ia and latest_prescription.investigation_advised:
                ia = latest_prescription.investigation_advised
            if not pd and latest_prescription.provisional_diagnosis:
                pd = latest_prescription.provisional_diagnosis
            if not special_note and latest_prescription.notes:
                special_note = latest_prescription.notes
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
        'pc': pc,
        'dev': dev,
        'vac': vac,
        'me': me,
        'ia': ia,
        'pd': pd,
        'special_note': special_note,
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
                            qty=med_data.get('qty', 1),
                            dosage_form=med_data.get('dosage_form', 'MG'),
                            days=med_data.get('days', 1),
                            frequency=med_data.get('frequency', 'OD'),
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
                qty=data.get('qty', 1),
                dosage_form=data.get('dosage_form', 'MG'),
                days=data.get('days', 1),
                frequency=data.get('frequency', 'OD'),
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
                'qty': float(med.qty) if med.qty else 1,
                'dosage_form': med.dosage_form,
                'frequency': med.frequency,
                'days': med.days,
                'notes': med.notes,
                'category': med.medicine.category.name if med.medicine.category else '',
                'dosage': med.medicine.weight_or_quantity or '',
                'stock': med.medicine.total_items
            })
        
        # Include clinical notes from the template
        return JsonResponse({
            'success': True, 
            'medicines': results,
            'clinical_notes': {
                'presenting_complaints': template.presenting_complaints or '',
                'development': template.development or '',
                'vaccination': template.vaccination or '',
                'medical_examination': template.medical_examination or '',
                'investigation_advised': template.investigation_advised or '',
                'provisional_diagnosis': template.provisional_diagnosis or ''
            }
        })
        
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
    today = timezone.localtime(timezone.now()).date()
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
        today = timezone.localtime(timezone.now()).date()
        
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


def patient_detail_api(request, ref_no):
    """API endpoint to get full patient details and all prescriptions history"""
    try:
        patient = Patient.objects.get(ref_no=ref_no)
        
        # Get all prescriptions for this patient grouped by batch_id
        all_prescriptions = Prescription.objects.filter(
            patient=patient
        ).select_related('medicine').order_by('-created_at')
        
        # Group prescriptions by batch_id (visit/session)
        visits = {}
        for presc in all_prescriptions:
            batch_key = str(presc.batch_id) if presc.batch_id else f"single_{presc.id}"
            if batch_key not in visits:
                visits[batch_key] = {
                    'batch_id': str(presc.batch_id) if presc.batch_id else None,
                    'date': presc.created_at.strftime('%d %b %Y'),
                    'time': presc.created_at.strftime('%I:%M %p'),
                    'created_at': presc.created_at.isoformat(),
                    'medicines': []
                }
            
            visits[batch_key]['medicines'].append({
                'id': str(presc.id),
                'medicine_name': presc.medicine.name if presc.medicine else 'Unknown',
                'medicine_form': presc.medicine.medicine_form if presc.medicine else 'tablet',
                'qty': float(presc.qty) if presc.qty else 1,
                'dosage_form': presc.dosage_form,
                'frequency': presc.frequency,
                'days': presc.days,
            })
        
        # Convert to list and sort by date (newest first)
        visits_list = list(visits.values())
        visits_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Patient details
        patient_data = {
            'ref_no': patient.ref_no,
            'name': patient.name,
            'phone': patient.phone or 'N/A',
            'age': patient.age or 'N/A',
            'weight': f"{patient.weight} kg" if patient.weight else 'N/A',
            'height': f"{patient.height} cm" if patient.height else 'N/A',
            'temperature': f"{patient.temperature} °C" if patient.temperature else 'N/A',
            'registered': patient.created_at.strftime('%d %b %Y, %I:%M %p') if patient.created_at else 'N/A',
            'total_visits': len(visits_list),
            'total_prescriptions': all_prescriptions.count(),
        }
        
        return JsonResponse({
            'success': True,
            'patient': patient_data,
            'visits': visits_list,
        })
        
    except Patient.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============ PATIENT QUEUE SYSTEM ============

def get_patient_queue(request):
    """Get all patients waiting in queue"""
    try:
        # Get patients with waiting or with_doctor status from today
        # Use localtime() to convert to configured TIME_ZONE before getting date
        today = timezone.localtime(timezone.now()).date()
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
