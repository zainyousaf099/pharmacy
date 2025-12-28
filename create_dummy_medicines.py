import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from inventory.models import Product, ProductCategory, Distributor
from decimal import Decimal
from datetime import date, timedelta

# Create categories
cat_tablet, _ = ProductCategory.objects.get_or_create(name='Tablets')
cat_syrup, _ = ProductCategory.objects.get_or_create(name='Syrups')
cat_capsule, _ = ProductCategory.objects.get_or_create(name='Capsules')
cat_injection, _ = ProductCategory.objects.get_or_create(name='Injections')

# Create distributors
dist1, _ = Distributor.objects.get_or_create(name='ABC Pharma', defaults={'phone': '0300-1234567', 'address': 'Lahore'})
dist2, _ = Distributor.objects.get_or_create(name='XYZ Medical', defaults={'phone': '0321-9876543', 'address': 'Karachi'})

# Create 10 dummy medicines
# items_per_product = strips in box, subitems_per_item = tablets per strip
medicines = [
    {'name': 'Panadol', 'weight': '500mg', 'category': cat_tablet, 'distributor': dist1, 'form': 'tablet', 'purchase': 150, 'sale': 200, 'boxes': 25, 'items_per_product': 10, 'subitems_per_item': 10},
    {'name': 'Brufen', 'weight': '400mg', 'category': cat_tablet, 'distributor': dist1, 'form': 'tablet', 'purchase': 120, 'sale': 160, 'boxes': 30, 'items_per_product': 10, 'subitems_per_item': 10},
    {'name': 'Augmentin', 'weight': '625mg', 'category': cat_tablet, 'distributor': dist2, 'form': 'tablet', 'purchase': 450, 'sale': 550, 'boxes': 15, 'items_per_product': 6, 'subitems_per_item': 1},
    {'name': 'Flagyl', 'weight': '400mg', 'category': cat_tablet, 'distributor': dist1, 'form': 'tablet', 'purchase': 80, 'sale': 110, 'boxes': 40, 'items_per_product': 10, 'subitems_per_item': 10},
    {'name': 'Amoxil Syrup', 'weight': '125mg/5ml', 'category': cat_syrup, 'distributor': dist2, 'form': 'syrup', 'purchase': 180, 'sale': 240, 'boxes': 20, 'items_per_product': 1, 'subitems_per_item': 1},
    {'name': 'Risek', 'weight': '20mg', 'category': cat_capsule, 'distributor': dist1, 'form': 'capsule', 'purchase': 350, 'sale': 450, 'boxes': 18, 'items_per_product': 14, 'subitems_per_item': 1},
    {'name': 'Calpol Syrup', 'weight': '120mg/5ml', 'category': cat_syrup, 'distributor': dist2, 'form': 'syrup', 'purchase': 150, 'sale': 200, 'boxes': 35, 'items_per_product': 1, 'subitems_per_item': 1},
    {'name': 'Voltral Injection', 'weight': '75mg/3ml', 'category': cat_injection, 'distributor': dist1, 'form': 'injection', 'purchase': 25, 'sale': 40, 'boxes': 50, 'items_per_product': 5, 'subitems_per_item': 1},
    {'name': 'Azomax', 'weight': '500mg', 'category': cat_capsule, 'distributor': dist2, 'form': 'capsule', 'purchase': 280, 'sale': 380, 'boxes': 22, 'items_per_product': 3, 'subitems_per_item': 1},
    {'name': 'Ponstan', 'weight': '250mg', 'category': cat_tablet, 'distributor': dist1, 'form': 'tablet', 'purchase': 100, 'sale': 140, 'boxes': 28, 'items_per_product': 10, 'subitems_per_item': 10},
]

for i, med in enumerate(medicines):
    # Calculate total items and subitems
    total_items = med['boxes'] * med['items_per_product']
    total_subitems = total_items * med['subitems_per_item']
    
    # Set expiry date (6-24 months from now)
    expiry = date.today() + timedelta(days=180 + (i * 60))
    
    Product.objects.create(
        name=med['name'],
        weight_or_quantity=med['weight'],
        category=med['category'],
        distributor=med['distributor'].name,  # distributor is CharField, not FK
        medicine_form=med['form'],
        purchase_price=Decimal(str(med['purchase'])),
        sale_price=Decimal(str(med['sale'])),
        total_boxes=Decimal(str(med['boxes'])),
        items_per_product=med['items_per_product'],
        subitems_per_item=med['subitems_per_item'],
        total_items=Decimal(str(total_items)),
        total_subitems=Decimal(str(total_subitems)),
        expiry_date=expiry,
        batch_no=f'BATCH-{i+1:03d}',
    )
    print(f'Created: {med["name"]} - {med["weight"]} (Stock: {med["boxes"]} boxes)')

print('\n10 dummy medicines created successfully!')
print(f'Categories: {ProductCategory.objects.count()}')
print(f'Distributors: {Distributor.objects.count()}')
print(f'Products: {Product.objects.count()}')
