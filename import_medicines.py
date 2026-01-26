"""
Script to import medicines from Excel file into the database.
Run with: python manage.py shell < import_medicines.py
Or: python import_medicines.py
"""

import os
import sys
import re
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import pandas as pd
from inventory.models import Product, Distributor
from decimal import Decimal

def parse_medicine_form(name):
    """Extract medicine form from name"""
    name_upper = name.upper()
    
    # Check for specific forms in the name
    if ' TAB' in name_upper or name_upper.endswith('TAB') or 'TABLET' in name_upper:
        return 'tablet'
    elif ' CAP' in name_upper or name_upper.endswith('CAP') or 'CAPS' in name_upper or 'CAPSULE' in name_upper:
        return 'capsule'
    elif ' SYP' in name_upper or ' SYRUP' in name_upper or name_upper.endswith('SYP') or name_upper.endswith('SYRUP'):
        return 'syrup'
    elif ' INJ' in name_upper or name_upper.endswith('INJ') or 'INJECTION' in name_upper or 'VIAL' in name_upper or 'AMP' in name_upper:
        return 'injection'
    elif ' DROP' in name_upper or name_upper.endswith('DROPS') or 'E/DROP' in name_upper or 'N/DROP' in name_upper or 'ORAL DROP' in name_upper:
        return 'drops'
    elif 'CREAM' in name_upper or 'OINTMENT' in name_upper or 'GEL' in name_upper or 'LOTION' in name_upper or 'OINT' in name_upper:
        return 'ointment'
    elif 'INHALER' in name_upper or 'INHALE' in name_upper or 'ROTACAP' in name_upper:
        return 'inhaler'
    elif 'SUPP' in name_upper or 'SUPPOSITORY' in name_upper:
        return 'suppository'
    elif 'SYRINGE' in name_upper or 'SYR ' in name_upper or 'D/SYR' in name_upper:
        return 'other'  # Medical devices
    else:
        return 'other'

def extract_dosage(name):
    """Extract dosage/strength from medicine name"""
    # Common patterns: 500MG, 250 MG, 100ML, 5%, etc.
    patterns = [
        r'(\d+(?:\.\d+)?\s*(?:MG|MCG|G|GM|ML|%|IU|MIU|U|UNIT|UNITS))',  # 500MG, 100ML, 5%
        r'(\d+(?:\.\d+)?(?:MG|MCG|G|GM|ML|%|IU|MIU|U))',  # 500MG without space
        r'(\d+/\d+\s*(?:MG|ML))',  # 250/5ML
    ]
    
    dosages = []
    name_upper = name.upper()
    
    for pattern in patterns:
        matches = re.findall(pattern, name_upper, re.IGNORECASE)
        dosages.extend(matches)
    
    if dosages:
        # Return unique dosages joined
        unique_dosages = []
        for d in dosages:
            d = d.strip()
            if d and d not in unique_dosages:
                unique_dosages.append(d)
        return ', '.join(unique_dosages[:3])  # Max 3 dosages
    
    return ''

def import_medicines():
    """Import medicines from Excel file"""
    excel_file = 'item & companies.xlsx'
    
    print("=" * 60)
    print("MEDICINE IMPORT SCRIPT")
    print("=" * 60)
    
    # Read items
    print("\nReading Excel file...")
    df = pd.read_excel(excel_file, sheet_name='items', header=None)
    medicines = df[0].dropna().unique().tolist()
    
    total = len(medicines)
    print(f"Found {total:,} unique medicines to import")
    
    # Read and create distributors/companies
    print("\nReading companies...")
    df_companies = pd.read_excel(excel_file, sheet_name='companies', header=None)
    companies = df_companies[0].dropna().unique().tolist()
    print(f"Found {len(companies):,} companies")
    
    # Create distributors
    print("\nCreating distributors...")
    created_distributors = 0
    for company in companies:
        company_name = str(company).strip()
        if company_name:
            _, created = Distributor.objects.get_or_create(name=company_name)
            if created:
                created_distributors += 1
    print(f"Created {created_distributors} new distributors")
    
    # Import medicines in batches
    print("\nImporting medicines...")
    batch_size = 1000
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    products_to_create = []
    existing_names = set(Product.objects.values_list('name', flat=True))
    
    for i, medicine_name in enumerate(medicines):
        medicine_name = str(medicine_name).strip()
        
        if not medicine_name:
            continue
            
        # Skip if already exists
        if medicine_name in existing_names:
            skipped_count += 1
            continue
        
        try:
            # Parse medicine details
            medicine_form = parse_medicine_form(medicine_name)
            dosage = extract_dosage(medicine_name)
            
            product = Product(
                name=medicine_name,
                medicine_form=medicine_form,
                weight_or_quantity=dosage if dosage else None,
                products_in_box=1,
                items_per_product=1,
                subitems_per_item=1,
                purchase_price=Decimal('0.00'),
                sale_price=Decimal('0.00'),
            )
            products_to_create.append(product)
            existing_names.add(medicine_name)
            
            # Batch insert
            if len(products_to_create) >= batch_size:
                Product.objects.bulk_create(products_to_create, ignore_conflicts=True)
                created_count += len(products_to_create)
                products_to_create = []
                print(f"  Progress: {i+1:,}/{total:,} ({((i+1)/total*100):.1f}%) - Created: {created_count:,}")
                
        except Exception as e:
            error_count += 1
            if error_count <= 10:
                print(f"  Error with '{medicine_name}': {e}")
    
    # Insert remaining
    if products_to_create:
        Product.objects.bulk_create(products_to_create, ignore_conflicts=True)
        created_count += len(products_to_create)
    
    print("\n" + "=" * 60)
    print("IMPORT COMPLETE!")
    print("=" * 60)
    print(f"Total medicines in file: {total:,}")
    print(f"Created: {created_count:,}")
    print(f"Skipped (already exist): {skipped_count:,}")
    print(f"Errors: {error_count:,}")
    print(f"Total products in database: {Product.objects.count():,}")
    print("=" * 60)

if __name__ == '__main__':
    import_medicines()
