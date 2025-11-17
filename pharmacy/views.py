from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from opd.models import Patient
from doctor.models import Prescription
from inventory.models import Product
import json

# Create your views here.
def pharmacypanel(request):
    return render(request, 'pharmacytemp/dashboard.html')


def search_patient_prescription(request):
    """API endpoint to search patient and get their prescriptions"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'success': False, 'error': 'Search query is required'})
    
    try:
        # Search by reference number or name
        patient = Patient.objects.filter(ref_no__iexact=query).first()
        if not patient:
            patient = Patient.objects.filter(name__icontains=query).first()
        
        if not patient:
            return JsonResponse({'success': False, 'error': 'Patient not found'})
        
        # Get patient's latest prescriptions
        prescriptions = Prescription.objects.filter(patient=patient).select_related('medicine').order_by('-created_at')[:20]
        
        if not prescriptions.exists():
            return JsonResponse({
                'success': False,
                'error': 'No prescriptions found for this patient',
                'patient': {
                    'ref_no': patient.ref_no,
                    'name': patient.name,
                    'phone': patient.phone or 'N/A',
                    'age': patient.age or 'N/A',
                }
            })
        
        # Prepare prescription data
        prescription_data = []
        for rx in prescriptions:
            # Get timing information
            timing_parts = []
            if rx.morning:
                timing_parts.append('Morning')
            if rx.evening:
                timing_parts.append('Evening')
            if rx.night:
                timing_parts.append('Night')
            timing = ', '.join(timing_parts) if timing_parts else 'As directed'
            
            prescription_data.append({
                'id': str(rx.id),
                'medicine_name': rx.medicine.name,
                'medicine_id': str(rx.medicine.id),
                'days': rx.days,
                'timing': timing,
                'morning': rx.morning,
                'evening': rx.evening,
                'night': rx.night,
                'price': float(rx.medicine.sale_price_per_item) if rx.medicine.sale_price_per_item else 0.0,
                'category': rx.medicine.category.name if rx.medicine.category else 'N/A',
                'stock': rx.medicine.total_items,
                'notes': rx.notes or ''
            })
        
        # Patient details
        patient_details = f"""Reference No: {patient.ref_no}
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
                'phone': patient.phone or 'N/A',
                'age': patient.age or 'N/A',
                'details': patient_details
            },
            'prescriptions': prescription_data,
            'total_medicines': len(prescription_data)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def process_pharmacy_order(request):
    """API endpoint to process pharmacy order and save bill"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            patient_ref_no = data.get('patient_ref_no')
            medicines = data.get('medicines', [])
            total_amount = data.get('total_amount', 0)
            
            if not patient_ref_no:
                return JsonResponse({'success': False, 'error': 'Patient reference number is required'})
            
            if not medicines:
                return JsonResponse({'success': False, 'error': 'No medicines to process'})
            
            # Get patient
            try:
                patient = Patient.objects.get(ref_no=patient_ref_no)
            except Patient.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Patient not found'})
            
            # Here you can save the order/bill to a PharmacyBill model if needed
            # For now, we'll just return success
            
            return JsonResponse({
                'success': True,
                'message': 'Order processed successfully',
                'patient_name': patient.name,
                'total_amount': total_amount,
                'items_count': len(medicines)
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})