"""
Management command to load commonly used medicines in Pakistan
Run: python manage.py load_pakistan_medicines
"""

from django.core.management.base import BaseCommand
from inventory.models import Product, ProductCategory
from decimal import Decimal


class Command(BaseCommand):
    help = 'Load commonly used medicines in Pakistan with zero stock and current market prices'

    def handle(self, *args, **options):
        # Create categories if they don't exist
        categories = {
            'Tablets': ProductCategory.objects.get_or_create(name='Tablets')[0],
            'Capsules': ProductCategory.objects.get_or_create(name='Capsules')[0],
            'Syrups': ProductCategory.objects.get_or_create(name='Syrups')[0],
            'Injections': ProductCategory.objects.get_or_create(name='Injections')[0],
            'Drops': ProductCategory.objects.get_or_create(name='Drops')[0],
            'Ointments': ProductCategory.objects.get_or_create(name='Ointments')[0],
            'Inhalers': ProductCategory.objects.get_or_create(name='Inhalers')[0],
            'Sachets': ProductCategory.objects.get_or_create(name='Sachets')[0],
            'Suppositories': ProductCategory.objects.get_or_create(name='Suppositories')[0],
        }

        # Common Pakistani Medicines with approximate market prices (PKR)
        # Format: (name, weight/strength, medicine_form, category, sale_price_per_unit, items_per_box, subitems_per_item)
        
        medicines = [
            # ============ TABLETS ============
            # Pain Killers & Fever
            ('Panadol', '500mg', 'tablet', 'Tablets', 3.5, 10, 10),
            ('Panadol Extra', '500mg', 'tablet', 'Tablets', 5, 10, 10),
            ('Panadol CF', '500mg', 'tablet', 'Tablets', 8, 10, 10),
            ('Brufen', '200mg', 'tablet', 'Tablets', 4, 10, 10),
            ('Brufen', '400mg', 'tablet', 'Tablets', 6, 10, 10),
            ('Brufen', '600mg', 'tablet', 'Tablets', 8, 10, 10),
            ('Ponstan', '250mg', 'tablet', 'Tablets', 8, 10, 10),
            ('Ponstan', '500mg', 'tablet', 'Tablets', 12, 10, 10),
            ('Disprin', '300mg', 'tablet', 'Tablets', 2, 10, 10),
            ('Calpol', '500mg', 'tablet', 'Tablets', 4, 10, 10),
            ('Disprol', '120mg', 'tablet', 'Tablets', 3, 10, 10),
            ('Nurofen', '200mg', 'tablet', 'Tablets', 6, 10, 10),
            ('Tramal', '50mg', 'tablet', 'Tablets', 15, 10, 10),
            ('Tramal', '100mg', 'tablet', 'Tablets', 25, 10, 10),
            
            # Antibiotics
            ('Augmentin', '375mg', 'tablet', 'Tablets', 45, 6, 1),
            ('Augmentin', '625mg', 'tablet', 'Tablets', 70, 6, 1),
            ('Augmentin', '1g', 'tablet', 'Tablets', 95, 6, 1),
            ('Amoxil', '250mg', 'capsule', 'Capsules', 15, 10, 10),
            ('Amoxil', '500mg', 'capsule', 'Capsules', 25, 10, 10),
            ('Ciproxin', '250mg', 'tablet', 'Tablets', 30, 10, 10),
            ('Ciproxin', '500mg', 'tablet', 'Tablets', 45, 10, 10),
            ('Flagyl', '200mg', 'tablet', 'Tablets', 4, 10, 10),
            ('Flagyl', '400mg', 'tablet', 'Tablets', 6, 10, 10),
            ('Velosef', '250mg', 'capsule', 'Capsules', 25, 10, 10),
            ('Velosef', '500mg', 'capsule', 'Capsules', 40, 10, 10),
            ('Zinnat', '250mg', 'tablet', 'Tablets', 65, 10, 10),
            ('Zinnat', '500mg', 'tablet', 'Tablets', 95, 10, 10),
            ('Klaricid', '250mg', 'tablet', 'Tablets', 55, 10, 10),
            ('Klaricid', '500mg', 'tablet', 'Tablets', 85, 10, 10),
            ('Azomax', '250mg', 'tablet', 'Tablets', 50, 6, 1),
            ('Azomax', '500mg', 'tablet', 'Tablets', 75, 3, 1),
            ('Vibramycin', '100mg', 'capsule', 'Capsules', 20, 10, 10),
            ('Roxid', '150mg', 'tablet', 'Tablets', 45, 10, 10),
            ('Moxiget', '400mg', 'tablet', 'Tablets', 85, 5, 1),
            ('Levoflox', '500mg', 'tablet', 'Tablets', 35, 10, 10),
            ('Levoflox', '750mg', 'tablet', 'Tablets', 50, 5, 1),
            
            # Gastro / Antacids
            ('Risek', '20mg', 'capsule', 'Capsules', 18, 14, 1),
            ('Risek', '40mg', 'capsule', 'Capsules', 28, 14, 1),
            ('Nexium', '20mg', 'tablet', 'Tablets', 30, 14, 1),
            ('Nexium', '40mg', 'tablet', 'Tablets', 45, 14, 1),
            ('Zantac', '150mg', 'tablet', 'Tablets', 8, 10, 10),
            ('Motilium', '10mg', 'tablet', 'Tablets', 6, 10, 10),
            ('Maxolon', '10mg', 'tablet', 'Tablets', 5, 10, 10),
            ('Imodium', '2mg', 'capsule', 'Capsules', 8, 10, 10),
            ('Buscopan', '10mg', 'tablet', 'Tablets', 10, 10, 10),
            ('Cyclopam', '10mg', 'tablet', 'Tablets', 8, 10, 10),
            ('Gaviscon', '500mg', 'tablet', 'Tablets', 12, 16, 1),
            ('Mucaine Gel', '10ml', 'syrup', 'Syrups', 250, 1, 120),
            
            # Allergy / Antihistamines
            ('Atarax', '10mg', 'tablet', 'Tablets', 5, 10, 10),
            ('Atarax', '25mg', 'tablet', 'Tablets', 8, 10, 10),
            ('Claritine', '10mg', 'tablet', 'Tablets', 15, 10, 10),
            ('Zyrtec', '10mg', 'tablet', 'Tablets', 12, 10, 10),
            ('Telfast', '120mg', 'tablet', 'Tablets', 25, 10, 10),
            ('Telfast', '180mg', 'tablet', 'Tablets', 35, 10, 10),
            ('Phenergan', '25mg', 'tablet', 'Tablets', 5, 10, 10),
            ('Benadryl', '25mg', 'tablet', 'Tablets', 6, 10, 10),
            ('Avil', '25mg', 'tablet', 'Tablets', 4, 10, 10),
            ('Montair', '4mg', 'tablet', 'Tablets', 25, 10, 10),
            ('Montair', '10mg', 'tablet', 'Tablets', 35, 10, 10),
            
            # Blood Pressure / Heart
            ('Lopressor', '50mg', 'tablet', 'Tablets', 8, 10, 10),
            ('Lopressor', '100mg', 'tablet', 'Tablets', 12, 10, 10),
            ('Norvasc', '5mg', 'tablet', 'Tablets', 15, 10, 10),
            ('Norvasc', '10mg', 'tablet', 'Tablets', 20, 10, 10),
            ('Concor', '2.5mg', 'tablet', 'Tablets', 12, 10, 10),
            ('Concor', '5mg', 'tablet', 'Tablets', 18, 10, 10),
            ('Capoten', '25mg', 'tablet', 'Tablets', 8, 10, 10),
            ('Capoten', '50mg', 'tablet', 'Tablets', 12, 10, 10),
            ('Cozaar', '50mg', 'tablet', 'Tablets', 25, 10, 10),
            ('Cozaar', '100mg', 'tablet', 'Tablets', 35, 10, 10),
            ('Cardace', '2.5mg', 'tablet', 'Tablets', 10, 10, 10),
            ('Cardace', '5mg', 'tablet', 'Tablets', 15, 10, 10),
            ('Aspirin', '75mg', 'tablet', 'Tablets', 2, 10, 10),
            ('Ecosprin', '75mg', 'tablet', 'Tablets', 3, 10, 10),
            ('Plavix', '75mg', 'tablet', 'Tablets', 35, 10, 10),
            
            # Diabetes
            ('Glucophage', '500mg', 'tablet', 'Tablets', 6, 10, 10),
            ('Glucophage', '850mg', 'tablet', 'Tablets', 8, 10, 10),
            ('Glucophage XR', '500mg', 'tablet', 'Tablets', 10, 10, 10),
            ('Diamicron', '80mg', 'tablet', 'Tablets', 15, 10, 10),
            ('Diamicron MR', '30mg', 'tablet', 'Tablets', 18, 10, 10),
            ('Amaryl', '1mg', 'tablet', 'Tablets', 12, 10, 10),
            ('Amaryl', '2mg', 'tablet', 'Tablets', 18, 10, 10),
            ('Januvia', '100mg', 'tablet', 'Tablets', 85, 14, 1),
            ('Galvus', '50mg', 'tablet', 'Tablets', 65, 14, 1),
            
            # Vitamins / Supplements
            ('Neurobion', '100mg', 'tablet', 'Tablets', 10, 10, 10),
            ('Centrum', '500mg', 'tablet', 'Tablets', 15, 30, 1),
            ('Caltrate', '600mg', 'tablet', 'Tablets', 12, 30, 1),
            ('Cal-C', '500mg', 'tablet', 'Tablets', 8, 10, 10),
            ('Fefol', '500mg', 'capsule', 'Capsules', 6, 10, 10),
            ('Surbex Z', '500mg', 'tablet', 'Tablets', 8, 30, 1),
            ('Folic Acid', '5mg', 'tablet', 'Tablets', 2, 10, 10),
            ('Ferrous Sulfate', '200mg', 'tablet', 'Tablets', 3, 10, 10),
            
            # Steroids / Anti-inflammatory
            ('Prednisone', '5mg', 'tablet', 'Tablets', 3, 10, 10),
            ('Prednisone', '10mg', 'tablet', 'Tablets', 5, 10, 10),
            ('Medrol', '4mg', 'tablet', 'Tablets', 15, 10, 10),
            ('Medrol', '8mg', 'tablet', 'Tablets', 25, 10, 10),
            ('Dexamethasone', '0.5mg', 'tablet', 'Tablets', 3, 10, 10),
            ('Betnesol', '0.5mg', 'tablet', 'Tablets', 4, 10, 10),
            
            # Cough / Cold / Respiratory
            ('Phensedyl', '100ml', 'syrup', 'Syrups', 150, 1, 100),
            ('Actifed', '120ml', 'syrup', 'Syrups', 180, 1, 120),
            ('Benylin', '100ml', 'syrup', 'Syrups', 160, 1, 100),
            ('Corex', '100ml', 'syrup', 'Syrups', 140, 1, 100),
            ('Ventolin', '2mg', 'tablet', 'Tablets', 4, 10, 10),
            ('Ventolin', '4mg', 'tablet', 'Tablets', 6, 10, 10),
            ('Theophylline', '100mg', 'tablet', 'Tablets', 5, 10, 10),
            ('Theophylline', '200mg', 'tablet', 'Tablets', 8, 10, 10),
            
            # Muscle Relaxants / Pain
            ('Myonal', '50mg', 'tablet', 'Tablets', 15, 10, 10),
            ('Relaxon', '500mg', 'tablet', 'Tablets', 8, 10, 10),
            ('Nucoxia', '60mg', 'tablet', 'Tablets', 18, 10, 10),
            ('Nucoxia', '90mg', 'tablet', 'Tablets', 22, 10, 10),
            ('Arcoxia', '60mg', 'tablet', 'Tablets', 35, 10, 10),
            ('Arcoxia', '90mg', 'tablet', 'Tablets', 45, 10, 10),
            ('Arcoxia', '120mg', 'tablet', 'Tablets', 55, 10, 10),
            
            # Anti-anxiety / Sleep
            ('Lexotanil', '3mg', 'tablet', 'Tablets', 8, 10, 10),
            ('Xanax', '0.25mg', 'tablet', 'Tablets', 6, 10, 10),
            ('Xanax', '0.5mg', 'tablet', 'Tablets', 10, 10, 10),
            ('Stilnoct', '10mg', 'tablet', 'Tablets', 25, 10, 10),
            
            # ============ SYRUPS ============
            # Fever / Pain Syrups (Pediatric)
            ('Calpol Syrup', '120mg/5ml', 'syrup', 'Syrups', 180, 1, 60),
            ('Calpol Syrup', '250mg/5ml', 'syrup', 'Syrups', 220, 1, 60),
            ('Brufen Syrup', '100mg/5ml', 'syrup', 'Syrups', 200, 1, 60),
            ('Ponstan Syrup', '50mg/5ml', 'syrup', 'Syrups', 250, 1, 60),
            ('Panadol Baby Drops', '100mg/ml', 'drops', 'Drops', 180, 1, 15),
            
            # Antibiotic Syrups
            ('Augmentin Syrup', '156mg/5ml', 'syrup', 'Syrups', 350, 1, 70),
            ('Augmentin Syrup', '312mg/5ml', 'syrup', 'Syrups', 450, 1, 70),
            ('Augmentin Syrup', '457mg/5ml', 'syrup', 'Syrups', 550, 1, 70),
            ('Amoxil Syrup', '125mg/5ml', 'syrup', 'Syrups', 180, 1, 60),
            ('Amoxil Syrup', '250mg/5ml', 'syrup', 'Syrups', 250, 1, 60),
            ('Velosef Syrup', '125mg/5ml', 'syrup', 'Syrups', 250, 1, 60),
            ('Velosef Syrup', '250mg/5ml', 'syrup', 'Syrups', 350, 1, 60),
            ('Zinnat Syrup', '125mg/5ml', 'syrup', 'Syrups', 400, 1, 50),
            ('Azomax Syrup', '200mg/5ml', 'syrup', 'Syrups', 380, 1, 15),
            ('Klaricid Syrup', '125mg/5ml', 'syrup', 'Syrups', 450, 1, 60),
            ('Klaricid Syrup', '250mg/5ml', 'syrup', 'Syrups', 550, 1, 60),
            ('Flagyl Syrup', '200mg/5ml', 'syrup', 'Syrups', 120, 1, 60),
            
            # Cough Syrups
            ('Phenergan Syrup', '5mg/5ml', 'syrup', 'Syrups', 120, 1, 60),
            ('Grilinctus Syrup', '100ml', 'syrup', 'Syrups', 150, 1, 100),
            ('Prospan Syrup', '100ml', 'syrup', 'Syrups', 400, 1, 100),
            ('Ambroxol Syrup', '15mg/5ml', 'syrup', 'Syrups', 100, 1, 60),
            ('Ventolin Syrup', '2mg/5ml', 'syrup', 'Syrups', 150, 1, 60),
            
            # Allergy Syrups
            ('Zyrtec Syrup', '5mg/5ml', 'syrup', 'Syrups', 200, 1, 60),
            ('Claritine Syrup', '5mg/5ml', 'syrup', 'Syrups', 250, 1, 60),
            ('Atarax Syrup', '10mg/5ml', 'syrup', 'Syrups', 180, 1, 60),
            ('Montair Syrup', '4mg/5ml', 'syrup', 'Syrups', 300, 1, 60),
            
            # GI Syrups
            ('Motilium Syrup', '1mg/ml', 'syrup', 'Syrups', 180, 1, 30),
            ('Flagyl Suspension', '200mg/5ml', 'syrup', 'Syrups', 120, 1, 60),
            ('Risek Suspension', '2mg/ml', 'syrup', 'Syrups', 350, 1, 30),
            
            # Multivitamin Syrups
            ('Iberet Syrup', '100ml', 'syrup', 'Syrups', 220, 1, 100),
            ('Sangobion Syrup', '100ml', 'syrup', 'Syrups', 250, 1, 100),
            ('Vidaylin Syrup', '120ml', 'syrup', 'Syrups', 280, 1, 120),
            ('Ostocalcium Syrup', '200ml', 'syrup', 'Syrups', 350, 1, 200),
            
            # ============ INJECTIONS ============
            # Pain / Fever Injections
            ('Paracetamol Injection', '1g', 'injection', 'Injections', 150, 5, 1),
            ('Ketorolac Injection', '30mg', 'injection', 'Injections', 120, 5, 1),
            ('Diclofenac Injection', '75mg', 'injection', 'Injections', 80, 5, 1),
            ('Tramadol Injection', '100mg', 'injection', 'Injections', 100, 5, 1),
            ('Nalbuphine Injection', '10mg', 'injection', 'Injections', 150, 5, 1),
            
            # Antibiotic Injections
            ('Augmentin Injection', '1.2g', 'injection', 'Injections', 350, 1, 1),
            ('Ceftriaxone Injection', '500mg', 'injection', 'Injections', 120, 1, 1),
            ('Ceftriaxone Injection', '1g', 'injection', 'Injections', 180, 1, 1),
            ('Ceftriaxone Injection', '2g', 'injection', 'Injections', 280, 1, 1),
            ('Ciprofloxacin Injection', '200mg', 'injection', 'Injections', 250, 1, 1),
            ('Amikacin Injection', '500mg', 'injection', 'Injections', 180, 5, 1),
            ('Gentamicin Injection', '80mg', 'injection', 'Injections', 50, 5, 1),
            ('Vancomycin Injection', '500mg', 'injection', 'Injections', 450, 1, 1),
            ('Meropenem Injection', '500mg', 'injection', 'Injections', 650, 1, 1),
            ('Meropenem Injection', '1g', 'injection', 'Injections', 950, 1, 1),
            ('Sulzone Injection', '1.5g', 'injection', 'Injections', 350, 1, 1),
            
            # Steroid Injections
            ('Dexamethasone Injection', '4mg', 'injection', 'Injections', 50, 10, 1),
            ('Hydrocortisone Injection', '100mg', 'injection', 'Injections', 80, 1, 1),
            ('Solu-Medrol Injection', '40mg', 'injection', 'Injections', 250, 1, 1),
            ('Solu-Medrol Injection', '125mg', 'injection', 'Injections', 450, 1, 1),
            ('Solu-Medrol Injection', '500mg', 'injection', 'Injections', 850, 1, 1),
            ('Betnesol Injection', '4mg', 'injection', 'Injections', 60, 5, 1),
            
            # GI Injections
            ('Maxolon Injection', '10mg', 'injection', 'Injections', 40, 10, 1),
            ('Stemetil Injection', '12.5mg', 'injection', 'Injections', 50, 5, 1),
            ('Pantoprazole Injection', '40mg', 'injection', 'Injections', 180, 1, 1),
            ('Esomeprazole Injection', '40mg', 'injection', 'Injections', 250, 1, 1),
            
            # Respiratory Injections
            ('Aminophylline Injection', '250mg', 'injection', 'Injections', 40, 5, 1),
            ('Hydrocortisone Injection', '100mg', 'injection', 'Injections', 80, 1, 1),
            ('Adrenaline Injection', '1mg', 'injection', 'Injections', 35, 5, 1),
            
            # Anti-allergic Injections
            ('Avil Injection', '22.75mg', 'injection', 'Injections', 35, 5, 1),
            ('Phenergan Injection', '25mg', 'injection', 'Injections', 45, 5, 1),
            
            # Other Injections
            ('Calcium Gluconate Injection', '10ml', 'injection', 'Injections', 45, 5, 1),
            ('Vitamin K Injection', '10mg', 'injection', 'Injections', 55, 5, 1),
            ('Iron Sucrose Injection', '100mg', 'injection', 'Injections', 450, 5, 1),
            ('Lasix Injection', '20mg', 'injection', 'Injections', 35, 5, 1),
            ('Ranitidine Injection', '50mg', 'injection', 'Injections', 40, 5, 1),
            ('Buscopan Injection', '20mg', 'injection', 'Injections', 80, 5, 1),
            
            # IV Fluids
            ('Normal Saline', '500ml', 'injection', 'Injections', 80, 1, 1),
            ('Normal Saline', '1000ml', 'injection', 'Injections', 120, 1, 1),
            ('Ringer Lactate', '500ml', 'injection', 'Injections', 90, 1, 1),
            ('Ringer Lactate', '1000ml', 'injection', 'Injections', 130, 1, 1),
            ('Dextrose 5%', '500ml', 'injection', 'Injections', 85, 1, 1),
            ('Dextrose 5%', '1000ml', 'injection', 'Injections', 125, 1, 1),
            ('Dextrose Saline', '500ml', 'injection', 'Injections', 85, 1, 1),
            
            # ============ DROPS ============
            # Eye Drops
            ('Tobrex Eye Drops', '5ml', 'drops', 'Drops', 280, 1, 5),
            ('Chloramphenicol Eye Drops', '10ml', 'drops', 'Drops', 80, 1, 10),
            ('Dexamethasone Eye Drops', '5ml', 'drops', 'Drops', 120, 1, 5),
            ('Tobradex Eye Drops', '5ml', 'drops', 'Drops', 450, 1, 5),
            ('Refresh Tears', '15ml', 'drops', 'Drops', 350, 1, 15),
            ('Systane Eye Drops', '10ml', 'drops', 'Drops', 550, 1, 10),
            ('Visine Eye Drops', '15ml', 'drops', 'Drops', 280, 1, 15),
            
            # Ear Drops
            ('Otrivin Nasal Drops', '10ml', 'drops', 'Drops', 180, 1, 10),
            ('Otrivin Nasal Drops', '15ml', 'drops', 'Drops', 220, 1, 15),
            ('Otrivin Nasal Spray', '10ml', 'drops', 'Drops', 250, 1, 10),
            ('Nasivion Nasal Drops', '10ml', 'drops', 'Drops', 150, 1, 10),
            ('Nasivion Mini Drops', '5ml', 'drops', 'Drops', 120, 1, 5),
            ('Ciprofloxacin Ear Drops', '10ml', 'drops', 'Drops', 150, 1, 10),
            ('Otogesic Ear Drops', '10ml', 'drops', 'Drops', 180, 1, 10),
            ('Sofradex Ear Drops', '8ml', 'drops', 'Drops', 280, 1, 8),
            
            # Oral Drops (Pediatric)
            ('Colicaid Drops', '15ml', 'drops', 'Drops', 150, 1, 15),
            ('Infacol Drops', '50ml', 'drops', 'Drops', 350, 1, 50),
            ('Vitamin D Drops', '15ml', 'drops', 'Drops', 280, 1, 15),
            ('Ferrous Drops', '30ml', 'drops', 'Drops', 180, 1, 30),
            ('Multivitamin Drops', '30ml', 'drops', 'Drops', 220, 1, 30),
            
            # ============ OINTMENTS/CREAMS ============
            ('Polyfax Ointment', '20g', 'ointment', 'Ointments', 180, 1, 20),
            ('Fucidin Cream', '15g', 'ointment', 'Ointments', 350, 1, 15),
            ('Fucidin H Cream', '15g', 'ointment', 'Ointments', 400, 1, 15),
            ('Betnovate Cream', '15g', 'ointment', 'Ointments', 180, 1, 15),
            ('Betnovate N Cream', '15g', 'ointment', 'Ointments', 220, 1, 15),
            ('Dermovate Cream', '25g', 'ointment', 'Ointments', 350, 1, 25),
            ('Candistan Cream', '15g', 'ointment', 'Ointments', 150, 1, 15),
            ('Clotrimazole Cream', '15g', 'ointment', 'Ointments', 100, 1, 15),
            ('Daktarin Cream', '15g', 'ointment', 'Ointments', 280, 1, 15),
            ('Hydrocortisone Cream', '15g', 'ointment', 'Ointments', 120, 1, 15),
            ('Voltaren Gel', '50g', 'ointment', 'Ointments', 350, 1, 50),
            ('Brufen Gel', '50g', 'ointment', 'Ointments', 280, 1, 50),
            ('Diclofenac Gel', '30g', 'ointment', 'Ointments', 180, 1, 30),
            ('Soframycin Cream', '15g', 'ointment', 'Ointments', 120, 1, 15),
            ('Burnol Cream', '20g', 'ointment', 'Ointments', 100, 1, 20),
            ('Savlon Cream', '30g', 'ointment', 'Ointments', 150, 1, 30),
            ('Zinc Oxide Ointment', '30g', 'ointment', 'Ointments', 80, 1, 30),
            ('Vaseline', '50g', 'ointment', 'Ointments', 120, 1, 50),
            
            # ============ INHALERS ============
            ('Ventolin Inhaler', '100mcg', 'inhaler', 'Inhalers', 450, 1, 200),
            ('Seretide Inhaler', '25/125mcg', 'inhaler', 'Inhalers', 1800, 1, 120),
            ('Seretide Inhaler', '25/250mcg', 'inhaler', 'Inhalers', 2200, 1, 120),
            ('Symbicort Inhaler', '160/4.5mcg', 'inhaler', 'Inhalers', 2000, 1, 120),
            ('Foracort Inhaler', '200mcg', 'inhaler', 'Inhalers', 850, 1, 120),
            ('Budecort Inhaler', '200mcg', 'inhaler', 'Inhalers', 650, 1, 200),
            ('Atrovent Inhaler', '20mcg', 'inhaler', 'Inhalers', 550, 1, 200),
            ('Flixotide Inhaler', '125mcg', 'inhaler', 'Inhalers', 950, 1, 120),
            
            # ============ SACHETS ============
            ('ORS Sachet', '20g', 'sachet', 'Sachets', 15, 20, 1),
            ('Ensure Powder', '400g', 'sachet', 'Sachets', 2200, 1, 1),
            ('Pediasure', '400g', 'sachet', 'Sachets', 2500, 1, 1),
            ('Cerelac', '350g', 'sachet', 'Sachets', 950, 1, 1),
            ('Lactogen', '400g', 'sachet', 'Sachets', 1200, 1, 1),
            ('Movicol Sachet', '13.8g', 'sachet', 'Sachets', 80, 20, 1),
            ('Ispaghol Husk', '100g', 'sachet', 'Sachets', 150, 1, 1),
            
            # ============ SUPPOSITORIES ============
            ('Calpol Suppository', '125mg', 'suppository', 'Suppositories', 50, 5, 1),
            ('Calpol Suppository', '250mg', 'suppository', 'Suppositories', 65, 5, 1),
            ('Dulcolax Suppository', '10mg', 'suppository', 'Suppositories', 40, 5, 1),
            ('Glycerin Suppository', 'Adult', 'suppository', 'Suppositories', 35, 10, 1),
            ('Glycerin Suppository', 'Child', 'suppository', 'Suppositories', 30, 10, 1),
            ('Diclofenac Suppository', '100mg', 'suppository', 'Suppositories', 45, 5, 1),
        ]

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for med in medicines:
            name, strength, med_form, cat_name, price, items_per_box, subitems_per_item = med
            category = categories.get(cat_name)
            
            # Create full name with strength
            full_name = f"{name} ({strength})" if strength else name
            
            # Check if medicine already exists
            existing = Product.objects.filter(name__iexact=full_name).first()
            
            if existing:
                skipped_count += 1
                continue
            
            try:
                product = Product.objects.create(
                    name=full_name,
                    category=category,
                    medicine_form=med_form,
                    weight_or_quantity=strength,
                    
                    # Stock structure (zero stock)
                    products_in_box=0,  # 0 boxes
                    items_per_product=items_per_box,
                    subitems_per_item=subitems_per_item,
                    
                    # Pricing (approximate PKR prices)
                    purchase_price=Decimal(str(price * 0.8)),  # 80% of sale price as purchase
                    purchase_margin_percent=Decimal('25'),
                    sale_price=Decimal(str(price)),  # Per strip/bottle price
                    sale_price_per_subitem=Decimal(str(round(price / subitems_per_item, 2))),  # Per tablet price
                    
                    # Additional info
                    rack_no='',
                    batch_no='',
                )
                created_count += 1
                self.stdout.write(f'  ✓ Added: {full_name}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error adding {full_name}: {str(e)}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'=' * 50))
        self.stdout.write(self.style.SUCCESS(f'Total medicines added: {created_count}'))
        self.stdout.write(self.style.WARNING(f'Skipped (already exist): {skipped_count}'))
        self.stdout.write(self.style.SUCCESS(f'=' * 50))
        self.stdout.write('')
        self.stdout.write('All medicines added with ZERO stock.')
        self.stdout.write('Add stock from inventory when you purchase from distributors.')
