from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from opd.models import Patient
from admission.models import AdmittedPatient, Room, Bed, MedicineCharge, OtherCharge
import json

# ============= DOCTOR VIEWS =============

@csrf_exempt
def admit_patient(request):
    """Doctor admits a patient"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            patient_ref = data.get('patient_ref')
            admission_reason = data.get('admission_reason', '')
            initial_diagnosis = data.get('initial_diagnosis', '')
            
            if not patient_ref:
                return JsonResponse({'success': False, 'error': 'Patient reference required'})
            
            patient = get_object_or_404(Patient, ref_no=patient_ref)
            
            # Check if patient is already admitted
            existing = AdmittedPatient.objects.filter(
                opd_patient=patient, 
                status='admitted'
            ).exists()
            
            if existing:
                return JsonResponse({
                    'success': False, 
                    'error': 'Patient is already admitted'
                })
            
            # Create admission
            admission = AdmittedPatient.objects.create(
                opd_patient=patient,
                admission_reason=admission_reason,
                initial_diagnosis=initial_diagnosis,
                admitted_by=request.user.staffid if hasattr(request.user, 'staffid') else None
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Patient admitted successfully. Admission No: {admission.admission_number}',
                'admission_number': admission.admission_number
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def doctor_admitted_patients_list(request):
    """View list of all admitted patients for doctors"""
    admitted_patients = AdmittedPatient.objects.filter(
        status='admitted'
    ).select_related('opd_patient', 'room', 'bed').order_by('-admission_date')
    
    context = {
        'admitted_patients': admitted_patients,
    }
    return render(request, 'doctortemp/admitted_patients_list.html', context)


# ============= OPD RECEPTION VIEWS =============

def admitted_patients_list(request):
    """View list of all admitted patients for OPD reception"""
    admitted_patients = AdmittedPatient.objects.filter(
        status='admitted'
    ).select_related('opd_patient', 'room', 'bed').order_by('-admission_date')
    
    # Get patients needing room assignment
    needs_room = admitted_patients.filter(room__isnull=True)
    
    context = {
        'admitted_patients': admitted_patients,
        'needs_room': needs_room,
    }
    return render(request, 'opdtemp/admitted_patients_list.html', context)


def assign_room_bed(request, admission_id):
    """Assign room and bed to admitted patient"""
    admission = get_object_or_404(AdmittedPatient, id=admission_id, status='admitted')
    
    if request.method == 'POST':
        try:
            room_id = request.POST.get('room_id')
            bed_id = request.POST.get('bed_id')
            
            with transaction.atomic():
                # Free previous bed if exists
                if admission.bed:
                    admission.bed.is_occupied = False
                    admission.bed.save()
                
                # Assign new room and bed
                if room_id:
                    room = get_object_or_404(Room, id=room_id, is_active=True)
                    admission.room = room
                
                if bed_id:
                    bed = get_object_or_404(Bed, id=bed_id, is_occupied=False)
                    bed.is_occupied = True
                    bed.save()
                    admission.bed = bed
                
                admission.save()
                
                messages.success(request, 'Room and bed assigned successfully')
                return redirect('admitted_patients_list')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    # Get available rooms and beds
    rooms = Room.objects.filter(is_active=True).prefetch_related('beds')
    
    context = {
        'admission': admission,
        'rooms': rooms,
    }
    return render(request, 'opdtemp/assign_room_bed.html', context)


@csrf_exempt
def get_available_beds(request):
    """API to get available beds for a room"""
    room_id = request.GET.get('room_id')
    
    if not room_id:
        return JsonResponse({'success': False, 'error': 'Room ID required'})
    
    try:
        beds = Bed.objects.filter(room_id=room_id, is_occupied=False)
        beds_data = [{'id': bed.id, 'bed_number': bed.bed_number} for bed in beds]
        
        return JsonResponse({'success': True, 'beds': beds_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def discharge_patient(request, admission_id):
    """Discharge patient with final billing"""
    admission = get_object_or_404(AdmittedPatient, id=admission_id, status='admitted')
    
    if request.method == 'POST':
        try:
            discharge_summary = request.POST.get('discharge_summary', '')
            
            with transaction.atomic():
                # Free the bed
                if admission.bed:
                    admission.bed.is_occupied = False
                    admission.bed.save()
                
                # Update admission
                admission.status = 'discharged'
                admission.discharge_date = timezone.now()
                admission.discharge_summary = discharge_summary
                admission.save()
                
                messages.success(request, f'Patient discharged successfully. Please go to Pharmacy to view/print the bill.')
                return redirect('admitted_patients_list')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    # Calculate all charges
    context = {
        'admission': admission,
        'room_charges': admission.total_room_charges(),
        'medicine_charges': admission.medicine_charges.all(),
        'other_charges': admission.other_charges.all(),
        'total_medicine': admission.total_medicine_charges(),
        'total_other': admission.total_other_charges(),
        'grand_total': admission.grand_total(),
    }
    return render(request, 'opdtemp/discharge_patient.html', context)


def discharge_billing(request, admission_id):
    """View final bill after discharge"""
    admission = get_object_or_404(AdmittedPatient, id=admission_id, status='discharged')
    
    # Calculate duration
    duration_days = (admission.discharge_date - admission.admission_date).days + 1
    
    context = {
        'admission': admission,
        'duration_days': duration_days,
        'room_charges': admission.total_room_charges(),
        'medicine_charges': admission.medicine_charges.all(),
        'other_charges': admission.other_charges.all(),
        'total_medicine': admission.total_medicine_charges(),
        'total_other': admission.total_other_charges(),
        'grand_total': admission.grand_total(),
    }
    return render(request, 'opdtemp/discharge_billing.html', context)


@csrf_exempt
def add_other_charge(request, admission_id):
    """Add other charges to admitted patient bill"""
    if request.method == 'POST':
        try:
            admission = get_object_or_404(AdmittedPatient, id=admission_id, status='admitted')
            
            description = request.POST.get('description')
            amount = request.POST.get('amount')
            
            if not description or not amount:
                return JsonResponse({'success': False, 'error': 'Description and amount required'})
            
            OtherCharge.objects.create(
                admitted_patient=admission,
                description=description,
                amount=amount,
                added_by=request.user.staffid if hasattr(request.user, 'staffid') else None
            )
            
            return JsonResponse({'success': True, 'message': 'Charge added successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def search_admitted_patient(request):
    """Search for admitted patient"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'success': False, 'error': 'Search query required'})
    
    try:
        # Search by admission number or patient name
        admission = AdmittedPatient.objects.filter(
            admission_number__icontains=query,
            status='admitted'
        ).select_related('opd_patient', 'room', 'bed').first()
        
        if not admission:
            admission = AdmittedPatient.objects.filter(
                opd_patient__name__icontains=query,
                status='admitted'
            ).select_related('opd_patient', 'room', 'bed').first()
        
        if not admission:
            return JsonResponse({'success': False, 'error': 'No admitted patient found'})
        
        return JsonResponse({
            'success': True,
            'patient': {
                'admission_id': str(admission.id),
                'admission_number': admission.admission_number,
                'name': admission.opd_patient.name,
                'ref_no': admission.opd_patient.ref_no,
                'phone': admission.opd_patient.phone or 'N/A',
                'age': admission.opd_patient.age or 'N/A',
                'room': f"{admission.room.room_number} - {admission.room.room_type}" if admission.room else 'Not Assigned',
                'bed': admission.bed.bed_number if admission.bed else 'N/A',
                'admission_date': admission.admission_date.strftime('%d %b %Y'),
                'admission_reason': admission.admission_reason,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
