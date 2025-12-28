from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from opd.models import Patient
from doctor.models import Prescription
from inventory.models import Product
from decimal import Decimal
import json
import os
import shutil
from pathlib import Path

# Create your views here.
def pharmacypanel(request):
    return render(request, 'pharmacytemp/dashboard.html')


def search_medicines_for_pharmacy(request):
    """API endpoint for medicine search in pharmacy (for direct sale)"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'success': False, 'medicines': []})
    
    try:
        # Search medicines by name
        medicines = Product.objects.filter(name__icontains=query)[:15]
        
        results = []
        for med in medicines:
            results.append({
                'id': med.id,
                'name': med.name,
                'medicine_form': med.medicine_form or 'tablet',
                'stock': med.total_items or 0,
                'sale_price': float(med.sale_price or 0),
                'sale_price_per_subitem': float(med.sale_price_per_subitem or 0),
                'category': med.category.name if med.category else 'N/A'
            })
        
        return JsonResponse({'success': True, 'medicines': results})
    except Exception as e:
        return JsonResponse({'success': False, 'medicines': [], 'error': str(e)})


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
        
        # Get patient's latest prescriptions from the most recent batch
        latest_prescription = Prescription.objects.filter(patient=patient).order_by('-created_at').first()
        
        if not latest_prescription:
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
            ).select_related('medicine').order_by('-created_at')[:20]
        
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
            
            # Get medicine form to determine pricing logic
            medicine_form = rx.medicine.medicine_form or 'tablet'
            
            # Liquid forms (syrup, drops, injection) - patient buys bottles, not doses
            # Solid forms (tablet, capsule) - patient buys individual tablets
            LIQUID_FORMS = ['syrup', 'drops', 'injection', 'inhaler', 'ointment']
            
            if medicine_form in LIQUID_FORMS:
                # For liquids: calculate how many bottles needed based on days
                # Usually 1 bottle = 60-100ml, enough for 5-7 days (3 doses/day, 5ml each)
                # Simple approach: 1 bottle for up to 7 days, 2 bottles for 8-14 days, etc.
                bottles_needed = max(1, (rx.days + 6) // 7)  # Round up to weeks
                
                # Use item price (per bottle) not subitem price
                price_per_bottle = float(rx.medicine.sale_price_per_item or rx.medicine.sale_price or 0)
                if price_per_bottle == 0:
                    price_per_bottle = float(rx.medicine.purchase_price_per_item or rx.medicine.purchase_price or 0)
                
                total_price = bottles_needed * price_per_bottle
                total_quantity = bottles_needed
                quantity_label = f"{bottles_needed} bottle(s)"
            else:
                # For solids (tablets, capsules): calculate total tablets needed
                doses_per_day = (1 if rx.morning else 0) + (1 if rx.evening else 0) + (1 if rx.night else 0)
                if doses_per_day == 0:
                    doses_per_day = 1
                total_quantity = doses_per_day * rx.days
                
                # Use subitem price (per tablet)
                price_per_unit = float(rx.medicine.sale_price_per_subitem) if rx.medicine.sale_price_per_subitem else 0.0
                total_price = total_quantity * price_per_unit
                quantity_label = f"{total_quantity} tablet(s)"
            
            prescription_data.append({
                'id': str(rx.id),
                'medicine_name': rx.medicine.name,
                'medicine_id': str(rx.medicine.id),
                'medicine_form': medicine_form,
                'days': rx.days,
                'timing': timing,
                'morning': rx.morning,
                'evening': rx.evening,
                'night': rx.night,
                'price': total_price,
                'quantity': total_quantity,
                'quantity_label': quantity_label,
                'category': rx.medicine.category.name if rx.medicine.category else 'N/A',
                'stock': rx.medicine.total_items,
                'notes': rx.notes or ''
            })
        
        # Patient details
        patient_details = f"""Reference No: {patient.ref_no}
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
    """API endpoint to process pharmacy order, deduct stock, and save bill"""
    from inventory.models import InventoryTransaction
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            patient_ref_no = data.get('patient_ref_no')
            medicines = data.get('medicines', [])
            total_amount = data.get('total_amount', 0)
            discount_amount = Decimal(str(data.get('discount_amount', 0)))
            discount_percentage = Decimal(str(data.get('discount_percentage', 0)))
            is_direct_sale = data.get('is_direct_sale', False)
            
            if not medicines:
                return JsonResponse({'success': False, 'error': 'No medicines to process'})
            
            # Get patient (optional for walk-in customers)
            patient = None
            patient_name = "Walk-in Customer"
            
            if patient_ref_no and not patient_ref_no.startswith('WALK-IN-'):
                try:
                    patient = Patient.objects.get(ref_no=patient_ref_no)
                    patient_name = patient.name
                except Patient.DoesNotExist:
                    # Allow processing without patient for direct sale
                    if not is_direct_sale:
                        return JsonResponse({'success': False, 'error': 'Patient not found'})
            
            # Get the latest batch of prescriptions for this patient (non-dispensed)
            batch_id = None
            if patient:
                latest_prescription = Prescription.objects.filter(
                    patient=patient, is_dispensed=False
                ).order_by('-created_at').first()
                batch_id = latest_prescription.batch_id if latest_prescription else None
            
            # Process each medicine - deduct stock and create transactions
            processed_items = []
            for med in medicines:
                medicine_id = med.get('medicine_id')
                medicine_name = med.get('medicine_name', '')
                days = int(med.get('days', 1))
                price = Decimal(str(med.get('price', 0)))
                
                if not medicine_id:
                    # For direct sale without medicine_id, skip stock deduction
                    processed_items.append({
                        'medicine': medicine_name,
                        'quantity': days,
                        'price': float(price),
                        'new_stock': 'N/A'
                    })
                    continue
                
                try:
                    product = Product.objects.get(id=medicine_id)
                except Product.DoesNotExist:
                    continue
                
                # Find the prescription for this medicine to get timing info
                prescription = None
                if patient and batch_id:
                    prescription = Prescription.objects.filter(
                        patient=patient,
                        medicine_id=medicine_id,
                        batch_id=batch_id,
                        is_dispensed=False
                    ).first()
                elif patient:
                    prescription = Prescription.objects.filter(
                        patient=patient,
                        medicine_id=medicine_id,
                        is_dispensed=False
                    ).first()
                
                # Get medicine form to determine quantity calculation
                medicine_form = product.medicine_form or 'tablet'
                LIQUID_FORMS = ['syrup', 'drops', 'injection', 'inhaler', 'ointment']
                
                if medicine_form in LIQUID_FORMS:
                    # For liquids: deduct bottles (items), not ml/doses
                    # 1 bottle for up to 7 days, 2 for 8-14 days, etc.
                    bottles_needed = max(1, (days + 6) // 7)
                    total_quantity = bottles_needed
                    
                    # Check bottle stock (total_items = bottles)
                    if product.total_items < total_quantity:
                        return JsonResponse({
                            'success': False, 
                            'error': f'Insufficient stock for {product.name}. Available: {int(product.total_items)} bottle(s), Required: {total_quantity}'
                        })
                    
                    # Create SALE transaction for bottles
                    sale_transaction = InventoryTransaction.objects.create(
                        product=product,
                        transaction_type=InventoryTransaction.SALE,
                        quantity_boxes=Decimal('0'),
                        quantity_items=Decimal(str(total_quantity)),  # Deduct items (bottles)
                        quantity_subitems=Decimal(str(total_quantity)),  # Also track as subitems
                        unit_purchase_price=product.purchase_price_per_item,
                        unit_sale_price=product.sale_price_per_item or product.purchase_price_per_item,
                        notes=f"Dispensed {total_quantity} bottle(s) to {patient_name} (Ref: {patient_ref_no or 'Direct Sale'}) - {days} days"
                    )
                else:
                    # For solids: deduct tablets (subitems)
                    # Get quantity from the passed data or calculate based on timing
                    qty_label = med.get('qty_label', '')
                    if qty_label and 'tablet' in qty_label.lower():
                        # Extract number from qty_label like "6 tablet(s)"
                        try:
                            total_quantity = int(''.join(filter(str.isdigit, qty_label.split()[0])))
                        except:
                            total_quantity = days
                    elif prescription:
                        doses_per_day = (1 if prescription.morning else 0) + \
                                       (1 if prescription.evening else 0) + \
                                       (1 if prescription.night else 0)
                        if doses_per_day == 0:
                            doses_per_day = 1
                        total_quantity = doses_per_day * days
                    else:
                        total_quantity = days
                    
                    # Check tablet stock
                    if product.total_subitems < total_quantity:
                        return JsonResponse({
                            'success': False, 
                            'error': f'Insufficient stock for {product.name}. Available: {int(product.total_subitems)} tablet(s), Required: {total_quantity}'
                        })
                    
                    # Create SALE transaction for tablets
                    sale_transaction = InventoryTransaction.objects.create(
                        product=product,
                        transaction_type=InventoryTransaction.SALE,
                        quantity_boxes=Decimal('0'),
                        quantity_items=Decimal('0'),
                        quantity_subitems=Decimal(str(total_quantity)),
                        unit_purchase_price=product.purchase_price_per_subitem,
                        unit_sale_price=product.sale_price_per_subitem or product.purchase_price_per_subitem,
                        notes=f"Dispensed {total_quantity} tablet(s) to {patient_name} (Ref: {patient_ref_no or 'Direct Sale'}) - {days} days"
                    )
                
                # Mark prescription as dispensed
                if prescription:
                    prescription.is_dispensed = True
                    prescription.dispensed_at = timezone.now()
                    prescription.save()
                
                # Refresh product to get updated stock after transaction
                product.refresh_from_db()
                
                # Get appropriate stock info based on medicine form
                if medicine_form in LIQUID_FORMS:
                    stock_info = f"{int(product.total_items)} bottle(s)"
                else:
                    stock_info = f"{int(product.total_subitems)} tablet(s)"
                
                processed_items.append({
                    'medicine': product.name,
                    'quantity': total_quantity,
                    'price': float(price),
                    'new_stock': stock_info
                })
            
            # Mark patient as completed in pharmacy queue after successful dispensing
            if patient and patient.pharmacy_queue_status in ['waiting', 'dispensing']:
                patient.pharmacy_queue_status = 'completed'
                patient.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Order processed successfully and stock updated',
                'patient_name': patient_name,
                'total_amount': float(total_amount),
                'items_count': len(processed_items),
                'processed_items': processed_items
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# Admission Patient Integration
def search_admitted_patient(request):
    """Search for admitted patients"""
    from admission.models import AdmittedPatient
    
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'success': False, 'error': 'Search query required'})
    
    try:
        # Search by admission number or patient name
        admitted = AdmittedPatient.objects.filter(
            admission_number__icontains=query,
            status='admitted'
        ).select_related('opd_patient', 'room', 'bed').first()
        
        if not admitted:
            # Try searching by patient name
            admitted = AdmittedPatient.objects.filter(
                opd_patient__name__icontains=query,
                status='admitted'
            ).select_related('opd_patient', 'room', 'bed').first()
        
        if not admitted:
            return JsonResponse({'success': False, 'error': 'No admitted patient found'})
        
        return JsonResponse({
            'success': True,
            'patient': {
                'admission_id': str(admitted.id),
                'admission_number': admitted.admission_number,
                'name': admitted.opd_patient.name,
                'ref_no': admitted.opd_patient.ref_no,
                'phone': admitted.opd_patient.phone or 'N/A',
                'age': admitted.opd_patient.age or 'N/A',
                'room': f"{admitted.room.room_number} - {admitted.room.room_type}" if admitted.room else 'Not Assigned',
                'bed': admitted.bed.bed_number if admitted.bed else 'N/A',
                'admission_date': admitted.admission_date.strftime('%d %b %Y'),
                'admission_reason': admitted.admission_reason,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def dispense_to_admitted(request):
    """Dispense medicines to admitted patient and add to bill"""
    from admission.models import AdmittedPatient, MedicineCharge
    from inventory.models import InventoryTransaction
    from django.utils import timezone
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            admission_id = data.get('admission_id')
            medicines = data.get('medicines', [])
            discount_amount = Decimal(str(data.get('discount_amount', 0)))
            discount_percentage = Decimal(str(data.get('discount_percentage', 0)))
            
            admitted_patient = AdmittedPatient.objects.get(id=admission_id, status='admitted')
            
            total_amount = Decimal('0')
            dispensed_items = []
            dispensed_medicine_ids = []  # Track dispensed medicine IDs
            
            for med in medicines:
                medicine_id = med.get('medicine_id')
                quantity = int(med.get('quantity', 1))
                
                try:
                    medicine = Product.objects.get(id=medicine_id)
                    
                    # Check stock (use total_subitems for accurate tracking)
                    if medicine.total_subitems < quantity:
                        return JsonResponse({
                            'success': False,
                            'error': f'Insufficient stock for {medicine.name}. Available: {int(medicine.total_subitems)}'
                        })
                    
                    # Use per subitem (tablet/unit) price
                    unit_price = medicine.sale_price_per_subitem or medicine.purchase_price_per_subitem
                    total_price = unit_price * Decimal(str(quantity))
                    
                    # Add to billing
                    MedicineCharge.objects.create(
                        admitted_patient=admitted_patient,
                        medicine_name=medicine.name,
                        quantity=quantity,
                        unit_price=unit_price,
                        prescription_reference=f"Pharmacy Dispense - {admitted_patient.admission_number}",
                        added_by=request.user.staffid if hasattr(request.user, 'staffid') else None
                    )
                    
                    # Create SALE transaction to properly track sales and deduct stock
                    InventoryTransaction.objects.create(
                        product=medicine,
                        transaction_type=InventoryTransaction.SALE,
                        quantity_boxes=Decimal('0'),
                        quantity_items=Decimal('0'),
                        quantity_subitems=Decimal(str(quantity)),
                        unit_purchase_price=medicine.purchase_price_per_subitem,
                        unit_sale_price=unit_price,
                        notes=f"Dispensed to admitted patient {admitted_patient.opd_patient.name} (Admission: {admitted_patient.admission_number})"
                    )
                    # Stock is automatically updated by InventoryTransaction.save() -> product.update_cached_stock()
                    
                    total_amount += total_price
                    dispensed_items.append({
                        'name': medicine.name,
                        'quantity': quantity,
                        'unit_price': float(unit_price),
                        'total_price': float(total_price)
                    })
                    
                    dispensed_medicine_ids.append(medicine_id)
                    
                except Product.DoesNotExist:
                    continue
            
            # Mark prescriptions as dispensed for this patient
            if dispensed_medicine_ids:
                Prescription.objects.filter(
                    patient=admitted_patient.opd_patient,
                    medicine_id__in=dispensed_medicine_ids,
                    is_dispensed=False
                ).update(
                    is_dispensed=True,
                    dispensed_at=timezone.now()
                )
            
            # Calculate final total after discount
            final_total = total_amount - discount_amount
            
            return JsonResponse({
                'success': True,
                'message': f'Medicines dispensed and added to bill. Total: Rs. {final_total:.2f}',
                'dispensed_items': dispensed_items,
                'total_amount': float(total_amount),
                'discount_amount': float(discount_amount),
                'discount_percentage': float(discount_percentage),
                'final_total': float(final_total),
                'patient_name': admitted_patient.opd_patient.name,
                'admission_number': admitted_patient.admission_number
            })
            
        except AdmittedPatient.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Patient not found or already discharged'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'pharmacytemp/dispense_admitted.html')


def admitted_patients_pharmacy(request):
    """View all admitted and recently discharged patients for pharmacy"""
    from admission.models import AdmittedPatient
    from datetime import timedelta
    
    # Get admitted patients
    admitted_patients = AdmittedPatient.objects.filter(
        status='admitted'
    ).select_related('opd_patient', 'room', 'bed').order_by('-admission_date')
    
    # Get recently discharged patients (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    discharged_patients = AdmittedPatient.objects.filter(
        status='discharged',
        discharge_date__gte=thirty_days_ago
    ).select_related('opd_patient', 'room', 'bed').order_by('-discharge_date')
    
    context = {
        'admitted_patients': admitted_patients,
        'discharged_patients': discharged_patients,
    }
    return render(request, 'pharmacytemp/admitted_patients.html', context)


def discharge_billing_pharmacy(request, admission_id):
    """View final bill for admitted patient - PHARMACY ONLY"""
    from admission.models import AdmittedPatient
    
    admission = get_object_or_404(AdmittedPatient, id=admission_id)
    
    # Calculate duration
    end_date = admission.discharge_date or timezone.now()
    duration_days = (end_date - admission.admission_date).days + 1
    
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
    return render(request, 'pharmacytemp/discharge_billing.html', context)


# ============ DATABASE BACKUP & RESTORE ============

def download_database(request):
    """Download the current database file as backup"""
    try:
        db_path = settings.DATABASES['default']['NAME']
        
        if not os.path.exists(db_path):
            return JsonResponse({'success': False, 'error': 'Database file not found'})
        
        # Create a backup copy with timestamp
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'clinic_backup_{timestamp}.sqlite3'
        
        # Read the database file
        response = FileResponse(
            open(db_path, 'rb'),
            as_attachment=True,
            filename=backup_filename
        )
        response['Content-Type'] = 'application/x-sqlite3'
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def upload_database(request):
    """Upload and restore a database backup with automatic migration"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        if 'database' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No database file uploaded'})
        
        uploaded_file = request.FILES['database']
        
        # Validate file extension
        if not uploaded_file.name.endswith('.sqlite3'):
            return JsonResponse({'success': False, 'error': 'Invalid file format. Please upload a .sqlite3 file'})
        
        # Get current database path
        db_path = settings.DATABASES['default']['NAME']
        
        # Create backup of current database before replacing
        if os.path.exists(db_path):
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_path = str(db_path).replace('.sqlite3', f'_backup_{timestamp}.sqlite3')
            shutil.copy2(db_path, backup_path)
        
        # Save uploaded database
        with open(db_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # ========== CRITICAL: Run migrations on restored database ==========
        # This ensures old backups work with new app versions that have new models/fields
        from django.core.management import call_command
        from io import StringIO
        
        migration_output = StringIO()
        migration_errors = StringIO()
        
        try:
            # Close all database connections to release the file
            from django import db
            db.connections.close_all()
            
            # Run migrations to update old database to current schema
            call_command('migrate', '--run-syncdb', verbosity=1, stdout=migration_output, stderr=migration_errors)
            
            migration_result = migration_output.getvalue()
            migration_err = migration_errors.getvalue()
            
            # Log migration results for debugging
            print(f"Migration output: {migration_result}")
            if migration_err:
                print(f"Migration errors: {migration_err}")
            
            return JsonResponse({
                'success': True, 
                'message': 'Database restored successfully! Migrations applied to ensure compatibility with current app version. Please restart the application.',
                'migrations_applied': True
            })
            
        except Exception as migrate_error:
            # Migration failed - but database is still restored
            print(f"Migration error after restore: {migrate_error}")
            return JsonResponse({
                'success': True, 
                'message': f'Database restored but migration had issues: {str(migrate_error)}. The app may need a manual restart.',
                'migrations_applied': False,
                'migration_error': str(migrate_error)
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_database_info(request):
    """Get information about current database"""
    try:
        db_path = settings.DATABASES['default']['NAME']
        
        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
            modified_time = os.path.getmtime(db_path)
            modified_datetime = timezone.datetime.fromtimestamp(modified_time)
            
            # Convert to human-readable size
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            
            return JsonResponse({
                'success': True,
                'path': str(db_path),
                'size': size_str,
                'last_modified': modified_datetime.strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            return JsonResponse({'success': False, 'error': 'Database file not found'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ==================== CLOUD BACKUP API ====================

def gdrive_status(request):
    """Check Google Drive connection status"""
    from .cloud_backup import check_auth_status
    
    status = check_auth_status()
    return JsonResponse(status)


@csrf_exempt
def gdrive_setup(request):
    """Setup Google Drive OAuth credentials"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    from .cloud_backup import setup_client_secrets
    
    try:
        data = json.loads(request.body)
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        
        if not client_id or not client_secret:
            return JsonResponse({'success': False, 'error': 'Client ID and Secret required'})
        
        result = setup_client_secrets(client_id, client_secret)
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def gdrive_auth_url(request):
    """Get Google Drive authentication URL"""
    from .cloud_backup import authenticate_gdrive
    
    result = authenticate_gdrive()
    return JsonResponse(result)


@csrf_exempt
def gdrive_auth_complete(request):
    """Complete Google Drive authentication with code"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    from .cloud_backup import authenticate_gdrive
    
    try:
        data = json.loads(request.body)
        auth_code = data.get('code')
        
        if not auth_code:
            return JsonResponse({'success': False, 'error': 'Authorization code required'})
        
        result = authenticate_gdrive(auth_code)
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def gdrive_backup(request):
    """Create backup and upload to Google Drive"""
    from .cloud_backup import create_local_backup, upload_to_gdrive
    
    try:
        db_path = settings.DATABASES['default']['NAME']
        
        # First create local backup
        local_result = create_local_backup(db_path)
        
        if not local_result['success']:
            return JsonResponse({
                'success': False,
                'error': f"Local backup failed: {local_result.get('error')}"
            })
        
        # Upload to Google Drive
        upload_result = upload_to_gdrive(local_result['backup_path'])
        
        if upload_result.get('needs_auth'):
            return JsonResponse({
                'success': False,
                'needs_auth': True,
                'error': 'Please connect to Google Drive first',
                'local_backup': local_result['backup_name']
            })
        
        if not upload_result['success']:
            return JsonResponse({
                'success': False,
                'error': f"Upload failed: {upload_result.get('error')}",
                'local_backup': local_result['backup_name']
            })
        
        return JsonResponse({
            'success': True,
            'message': 'Backup uploaded to Google Drive successfully!',
            'file_name': upload_result.get('file_name'),
            'web_link': upload_result.get('web_link'),
            'local_backup': local_result['backup_name']
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def gdrive_list_backups(request):
    """List all backups from Google Drive"""
    from .cloud_backup import list_backups
    
    result = list_backups()
    return JsonResponse(result)


@csrf_exempt
def gdrive_disconnect(request):
    """Disconnect from Google Drive"""
    from .cloud_backup import disconnect_gdrive
    
    result = disconnect_gdrive()
    return JsonResponse(result)


def check_daily_backup(request):
    """Check if daily backup is needed"""
    from .cloud_backup import should_backup_today, get_last_backup_date
    
    last_backup = get_last_backup_date()
    needs_backup = should_backup_today()
    
    return JsonResponse({
        'needs_backup': needs_backup,
        'last_backup': last_backup.strftime('%Y-%m-%d') if last_backup else None
    })


# ============== PHARMACY QUEUE SYSTEM ==============

def pharmacy_queue_api(request):
    """Get pharmacy queue - patients waiting for medicine after doctor visit"""
    today = timezone.now().date()
    
    # Get patients in pharmacy queue for today
    waiting_patients = Patient.objects.filter(
        pharmacy_queue_status='waiting',
        pharmacy_queued_at__date=today
    ).order_by('pharmacy_queue_number')
    
    dispensing_patients = Patient.objects.filter(
        pharmacy_queue_status='dispensing',
        pharmacy_queued_at__date=today
    ).order_by('pharmacy_queue_number')
    
    queue_data = []
    
    # Add dispensing patients first (currently being served)
    for patient in dispensing_patients:
        # Get count of undispensed prescriptions
        prescription_count = Prescription.objects.filter(
            patient=patient,
            is_dispensed=False
        ).count()
        
        queue_data.append({
            'id': patient.id,
            'reference_number': patient.ref_no,
            'name': patient.name,
            'age': patient.age or 'N/A',
            'queue_number': patient.pharmacy_queue_number,
            'queued_at': patient.pharmacy_queued_at.isoformat() if patient.pharmacy_queued_at else '',
            'status': 'dispensing',
            'prescription_count': prescription_count
        })
    
    # Add waiting patients
    for patient in waiting_patients:
        # Get count of undispensed prescriptions
        prescription_count = Prescription.objects.filter(
            patient=patient,
            is_dispensed=False
        ).count()
        
        queue_data.append({
            'id': patient.id,
            'reference_number': patient.ref_no,
            'name': patient.name,
            'age': patient.age or 'N/A',
            'queue_number': patient.pharmacy_queue_number,
            'queued_at': patient.pharmacy_queued_at.isoformat() if patient.pharmacy_queued_at else '',
            'status': 'waiting',
            'prescription_count': prescription_count
        })
    
    return JsonResponse({
        'success': True,
        'queue': queue_data,
        'waiting_count': waiting_patients.count(),
        'dispensing_count': dispensing_patients.count()
    })


@csrf_exempt
def pharmacy_queue_select(request, patient_id):
    """Select a patient from queue to start dispensing"""
    try:
        patient = Patient.objects.get(id=patient_id)
        patient.pharmacy_queue_status = 'dispensing'
        patient.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Now dispensing medicines for {patient.name}'
        })
    except Patient.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'})


@csrf_exempt
def pharmacy_queue_complete(request, patient_id):
    """Mark patient as completed (after dispensing medicines)"""
    try:
        patient = Patient.objects.get(id=patient_id)
        patient.pharmacy_queue_status = 'completed'
        patient.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Completed dispensing for {patient.name}'
        })
    except Patient.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'})

