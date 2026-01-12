from django.db import models
from django.utils import timezone
import uuid
from decimal import Decimal, ROUND_HALF_UP


def quantize_decimal(value, places=2):
    if value is None:
        return None
    q = Decimal(value).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)
    return q


class ProductCategory(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Distributor(models.Model):
    """Medicine distributor/supplier information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, help_text='Distributor/Supplier name')
    contact_person = models.CharField(max_length=255, blank=True, null=True, help_text='Contact person name')
    phone = models.CharField(max_length=20, blank=True, null=True, help_text='Phone number')
    email = models.EmailField(blank=True, null=True, help_text='Email address')
    address = models.TextField(blank=True, null=True, help_text='Complete address')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Top-level product model representing a product *box* (e.g. Panadol box).

    The model stores the purchase price at the level the user normally enters (assumed
    to be the price for the product unit they enter - typically a box). From that base
    price we compute prices for items and sub-items automatically based on
    products_in_box and sub_items_in_item counts.

    Example: products_in_box=1 (one box), items_per_product=10 (10 packs in a box),
    subitems_per_item=10 (10 tablets per pack). Then
      - purchase_price_per_item = purchase_price / items_per_product
      - purchase_price_per_subitem = purchase_price_per_item / subitems_per_item

    The model also stores sale prices; sale prices are optional. If not provided,
    they will be computed using the purchase_price and purchase_margin_percentage (profit %)
    or you can set explicit sale price fields.
    """
    
    MEDICINE_FORM_CHOICES = [
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('drops', 'Drops'),
        ('ointment', 'Ointment/Cream'),
        ('inhaler', 'Inhaler'),
        ('suppository', 'Suppository'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True)
    distributor = models.CharField(max_length=255, blank=True, null=True, help_text='Medicine distributor/supplier name')
    medicine_form = models.CharField(max_length=20, choices=MEDICINE_FORM_CHOICES, default='tablet', help_text='Form of medicine (tablet, syrup, injection, etc.)')

    # counts
    products_in_box = models.PositiveIntegerField(default=1, help_text='How many product-units in this entry (usually 1 box)')    
    items_per_product = models.PositiveIntegerField(default=1, help_text='How many items (eg packs) are inside one product unit (box)')
    subitems_per_item = models.PositiveIntegerField(default=1, help_text='How many sub-items (eg tablets) in each item')

    # weights/quantity
    weight_or_quantity = models.CharField(max_length=100, blank=True, null=True, help_text='Optional textual description of weight/volume/quantity') 

    # pricing (user enters purchase_price; derived fields computed)
    purchase_price = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0.0'), help_text='Purchase price for the product unit (usually a box)')
    purchase_price_per_item = models.DecimalField(max_digits=18, decimal_places=6, editable=False, default=Decimal('0.0'))
    purchase_price_per_subitem = models.DecimalField(max_digits=18, decimal_places=6, editable=False, default=Decimal('0.0'))

    # sale prices: you may set explicit sale prices; otherwise they will be computed
    sale_price = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True, help_text='Sale price for product unit')
    sale_price_per_item = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True, editable=False)
    sale_price_per_subitem = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True, editable=False)

    # margins and discount
    purchase_margin_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text='Expected margin percent to compute sale prices if sale prices not given')
    discount_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text='Discount percent to apply at sale time (informational)')
    
    # Distributor discount fields
    distributor_discount_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text='Discount percentage provided by distributor on purchase')
    distributor_discount_pkr = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'), help_text='Discount amount in PKR provided by distributor')
    net_purchase_price = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0.00'), help_text='Purchase price after distributor discount')

    # inventory & logistics
    rack_no = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(null=True, blank=True)
    inventory_receipt_date = models.DateField(default=timezone.now)
    batch_no = models.CharField(max_length=200, blank=True, null=True)

    # stock tracking (optional cached totals)
    total_boxes = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0.0'))
    total_items = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0.0'))
    total_subitems = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0.0'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return f"{self.name} ({self.id})"

    def save(self, *args, **kwargs):
        # ensure counts are >=1
        if self.products_in_box < 1:
            self.products_in_box = 1
        if self.items_per_product < 1:
            self.items_per_product = 1
        if self.subitems_per_item < 1:
            self.subitems_per_item = 1

        # Calculate net purchase price after distributor discount
        gross_price = Decimal(self.purchase_price or 0)
        
        # If discount PKR is provided, calculate percentage
        if self.distributor_discount_pkr and self.distributor_discount_pkr > 0:
            self.net_purchase_price = gross_price - Decimal(self.distributor_discount_pkr)
            if gross_price > 0:
                self.distributor_discount_percent = quantize_decimal(
                    (Decimal(self.distributor_discount_pkr) / gross_price) * 100, places=2
                )
        # If discount percentage is provided, calculate PKR
        elif self.distributor_discount_percent and self.distributor_discount_percent > 0:
            self.distributor_discount_pkr = quantize_decimal(
                gross_price * (Decimal(self.distributor_discount_percent) / 100), places=2
            )
            self.net_purchase_price = gross_price - self.distributor_discount_pkr
        else:
            self.net_purchase_price = gross_price
            self.distributor_discount_pkr = Decimal('0.00')
            self.distributor_discount_percent = Decimal('0.00')

        # compute purchase price per item and per subitem
        # Use NET purchase price (after discount) for calculations
        # The purchase_price is for the TOTAL quantity (products_in_box packs)
        # So if user enters 10 packs and purchase_price = 4000, then price per pack = 4000/10 = 400
        try:
            # price per single pack/box (using net price after discount)
            price_per_pack = Decimal(self.net_purchase_price) / Decimal(self.products_in_box)
        except Exception:
            price_per_pack = Decimal('0')

        # price per item (sheet/strip)
        try:
            self.purchase_price_per_item = quantize_decimal(price_per_pack / Decimal(self.items_per_product), places=6)
        except Exception:
            self.purchase_price_per_item = Decimal('0')

        # price per subitem (tablet/unit)
        try:
            self.purchase_price_per_subitem = quantize_decimal(self.purchase_price_per_item / Decimal(self.subitems_per_item), places=6)
        except Exception:
            self.purchase_price_per_subitem = Decimal('0')

        # compute sale prices if not provided using purchase_margin_percent
        if (self.sale_price is None or self.sale_price == Decimal('0')) and self.purchase_margin_percent:
            margin = Decimal(self.purchase_margin_percent) / Decimal('100')
            # sale price for total quantity (based on NET purchase price after discount)
            self.sale_price = quantize_decimal(Decimal(self.net_purchase_price) * (Decimal('1') + margin), places=6)

        # Calculate sale price per item and subitem
        if self.sale_price:
            try:
                sale_per_pack = Decimal(self.sale_price) / Decimal(self.products_in_box)
                self.sale_price_per_item = quantize_decimal(sale_per_pack / Decimal(self.items_per_product), places=6)
            except Exception:
                self.sale_price_per_item = Decimal('0')
            
            try:
                self.sale_price_per_subitem = quantize_decimal(self.sale_price_per_item / Decimal(self.subitems_per_item), places=6)
            except Exception:
                self.sale_price_per_subitem = Decimal('0')

        # update cached stock totals from InventoryTransaction records
        # Note: avoid heavy DB ops on save if used in loops; caching helps but you may
        # want to call Product.update_cached_stock() from management command or signals
        
        # Check if this is a new product - need to check using _state.adding instead of pk
        # because UUID fields get their value before save()
        is_new = self._state.adding
        skip_transaction = kwargs.pop('skip_initial_transaction', False)
        
        super().save(*args, **kwargs)
        
        # Initialize stock for new products by creating initial transaction
        # Note: InventoryTransaction.save() will automatically call product.update_cached_stock()
        if is_new and self.products_in_box > 0 and not skip_transaction:
            InventoryTransaction.objects.create(
                product=self,
                transaction_type='PUR',
                quantity_boxes=self.products_in_box,
                quantity_items=Decimal(self.products_in_box) * Decimal(self.items_per_product),
                quantity_subitems=Decimal(self.products_in_box) * Decimal(self.items_per_product) * Decimal(self.subitems_per_item),
                unit_purchase_price=self.purchase_price / Decimal(self.products_in_box) if self.products_in_box else Decimal('0'),
                notes=f"Initial stock for {self.name}"
            )

    # helper methods to compute on-the-fly values
    def price_per_product_unit(self):
        return quantize_decimal(Decimal(self.purchase_price) / Decimal(self.products_in_box), places=6)

    def compute_sale_price_from_margin(self, percent_margin: Decimal):
        margin = Decimal(percent_margin) / Decimal('100')
        return quantize_decimal(Decimal(self.purchase_price) * (Decimal('1') + margin), places=6)
    
    def get_unit_labels(self):
        """Return dynamic labels based on medicine form"""
        labels = {
            'tablet': {'item': 'Strip', 'subitem': 'Tablet'},
            'capsule': {'item': 'Strip', 'subitem': 'Capsule'},
            'syrup': {'item': 'Bottle', 'subitem': 'ml'},
            'injection': {'item': 'Vial/Ampoule', 'subitem': 'ml'},
            'drops': {'item': 'Bottle', 'subitem': 'ml'},
            'ointment': {'item': 'Tube', 'subitem': 'gram'},
            'inhaler': {'item': 'Inhaler', 'subitem': 'dose'},
            'suppository': {'item': 'Strip', 'subitem': 'Suppository'},
            'other': {'item': 'Unit', 'subitem': 'Piece'},
        }
        return labels.get(self.medicine_form, labels['tablet'])
    
    def get_display_stock(self):
        """Return formatted stock display based on medicine form"""
        labels = self.get_unit_labels()
        if self.medicine_form in ['syrup', 'injection', 'drops']:
            # For liquids, show bottles and ml
            return f"{self.total_items} {labels['item']}(s)"
        else:
            # For solids, show strips and tablets
            return f"{self.total_items} {labels['item']}(s), {self.total_subitems} {labels['subitem']}(s)"

    def update_cached_stock(self):
        """
        Calculate totals from InventoryTransaction records and cache them on model.
        
        Logic:
        - For liquid forms (syrup, drops, etc.): track items (bottles) directly
        - For solid forms (tablets, capsules): calculate items and boxes from subitems
        
        Example for tablets: 1 box = 4 strips, 1 strip = 10 tablets
        - If 40 tablets in stock: boxes=1, strips=4, tablets=40
        - If 30 tablets in stock: boxes=0, strips=3, tablets=30
        
        Example for syrups: track bottles directly
        - If 5 bottles in stock: items=5, subitems=5, boxes=0
        """
        # Liquid forms track by bottle (items), not by ml (subitems)
        LIQUID_FORMS = ['syrup', 'drops', 'injection', 'inhaler', 'ointment']
        is_liquid = self.medicine_form in LIQUID_FORMS
        
        # Sum all transactions - incoming quantities minus outgoing quantities
        aggregates = InventoryTransaction.objects.filter(product=self).aggregate(
            in_boxes=models.Sum('quantity_boxes'),
            out_boxes=models.Sum('quantity_boxes_out'),
            in_items=models.Sum('quantity_items'),
            out_items=models.Sum('quantity_items_out'),
            in_sub=models.Sum('quantity_subitems'),
            out_sub=models.Sum('quantity_subitems_out')
        )
        
        # For backward compat, if none exist, treat as zero
        in_items = aggregates.get('in_items') or Decimal('0')
        out_items = aggregates.get('out_items') or Decimal('0')
        in_sub = aggregates.get('in_sub') or Decimal('0')
        out_sub = aggregates.get('out_sub') or Decimal('0')
        
        if is_liquid:
            # For liquids: track by bottles (items)
            # Sales deduct from items, purchases add to items
            net_items = in_items - out_items
            if net_items < 0:
                net_items = Decimal('0')
            
            # For liquids, total_items = bottles, total_subitems can mirror items
            self.total_boxes = Decimal('0')  # Boxes not typically used for liquids
            self.total_items = quantize_decimal(net_items, places=6)
            self.total_subitems = quantize_decimal(net_items, places=6)  # Mirror for compatibility
        else:
            # For solids: Calculate net subitems (tablets)
            net_subitems = in_sub - out_sub
            if net_subitems < 0:
                net_subitems = Decimal('0')
            
            # Get product structure
            subitems_per_item = Decimal(str(self.subitems_per_item or 1))
            items_per_product = Decimal(str(self.items_per_product or 1))
            subitems_per_box = subitems_per_item * items_per_product  # tablets per box
            
            # Calculate boxes, items (strips), and remaining subitems from total subitems
            if subitems_per_box > 0:
                # How many complete boxes?
                complete_boxes = int(net_subitems // subitems_per_box)
                remaining_after_boxes = net_subitems - (Decimal(str(complete_boxes)) * subitems_per_box)
                
                # How many complete strips from remaining?
                if subitems_per_item > 0:
                    complete_items = int(remaining_after_boxes // subitems_per_item)
                    # Total items = items in complete boxes + additional complete items
                    total_items = (Decimal(str(complete_boxes)) * items_per_product) + Decimal(str(complete_items))
                else:
                    total_items = Decimal('0')
                
                total_boxes = Decimal(str(complete_boxes))
            else:
                total_boxes = Decimal('0')
                total_items = Decimal('0')
            
            # Store the values
            self.total_boxes = quantize_decimal(total_boxes, places=6)
            self.total_items = quantize_decimal(total_items, places=6)
            self.total_subitems = quantize_decimal(net_subitems, places=6)
        
        # Use direct update query to prevent triggering save() and creating new transactions
        Product.objects.filter(pk=self.pk).update(
            total_boxes=self.total_boxes,
            total_items=self.total_items,
            total_subitems=self.total_subitems
        )

    # convenience properties
    @property
    def current_stock_boxes(self):
        return self.total_boxes

    @property
    def current_stock_items(self):
        return self.total_items

    @property
    def current_stock_subitems(self):
        return self.total_subitems


class InventoryTransaction(models.Model):
    """
    Records incoming/outgoing stock. Quantities are stored in three parallel granularities:
      - quantity_boxes: how many boxes
      - quantity_items: how many items (packs)
      - quantity_subitems: how many sub-items (tablets)

    The model will also calculate derived quantities for convenience and reporting.
    """
    INCOMING = 'IN'
    OUTGOING = 'OUT'
    SALE = 'SALE'
    PURCHASE = 'PUR'

    TRANSACTION_TYPE_CHOICES = [
        (INCOMING, 'Incoming'),
        (OUTGOING, 'Outgoing'),
        (SALE, 'Sale'),
        (PURCHASE, 'Purchase'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPE_CHOICES)

    # quantities (use Decimal in case of fractional boxes/items for special cases)
    quantity_boxes = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'))
    quantity_items = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'))
    quantity_subitems = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'))

    # mirror fields for outgoing so aggregations are easy
    quantity_boxes_out = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'))
    quantity_items_out = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'))
    quantity_subitems_out = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'))

    unit_purchase_price = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'), help_text='Purchase price per product-unit at this transaction')
    unit_sale_price = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'), help_text='Sale price per product-unit at this transaction')

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # ensure quantities consistent: if outgoing or sale, populate outgoing mirror fields
        # and zero out the incoming fields to avoid double counting
        if self.transaction_type in {self.OUTGOING, self.SALE}:
            # For SALE/OUTGOING: store quantity in _out fields, zero out regular fields
            self.quantity_boxes_out = self.quantity_boxes
            self.quantity_items_out = self.quantity_items
            self.quantity_subitems_out = self.quantity_subitems
            # Zero out regular fields so they don't count as incoming
            self.quantity_boxes = Decimal('0')
            self.quantity_items = Decimal('0')
            self.quantity_subitems = Decimal('0')
        else:
            # incoming/purchase - keep quantities in regular fields, zero out _out fields
            self.quantity_boxes_out = Decimal('0')
            self.quantity_items_out = Decimal('0')
            self.quantity_subitems_out = Decimal('0')

        super().save(*args, **kwargs)

        # Update cached totals on product after transaction is saved
        self.product.update_cached_stock()

    def __str__(self):
        return f"Txn {self.id} {self.transaction_type} {self.product.name} - boxes:{self.quantity_boxes} items:{self.quantity_items} sub:{self.quantity_subitems}"


# Reporting helpers (can be used from views or management commands)
from django.db.models import Sum, F, ExpressionWrapper, DecimalField


def monthly_sales_report(year, month):
    """
    Return aggregated sales and purchases for all products in a given month.
    Output example:
      [{ 'product_id': <uuid>, 'name': 'Panadol', 'total_sold_subitems': Decimal(...), 'revenue': Decimal(...), 'cost': Decimal(...), 'profit': Decimal(...) }, ...]
    """
    from django.db.models import Q
    start = timezone.datetime(year=year, month=month, day=1)
    if month == 12:
        end = timezone.datetime(year=year + 1, month=1, day=1)
    else:
        end = timezone.datetime(year=year, month=month + 1, day=1)

    sales = InventoryTransaction.objects.filter(transaction_type=InventoryTransaction.SALE, created_at__gte=start, created_at__lt=end)
    grouped = sales.values('product').annotate(
        name=F('product__name'),
        total_subitems=Sum('quantity_subitems'),
        total_items=Sum('quantity_items'),
        total_boxes=Sum('quantity_boxes'),
        revenue=Sum(ExpressionWrapper(F('unit_sale_price') * F('quantity_boxes'), output_field=DecimalField(max_digits=18, decimal_places=6)))
    )
    # You can enhance to compute cost using product.purchase_price_per_subitem etc.
    return list(grouped)


def yearly_balance_sheet(year):
    """
    Very basic yearly balance summary: purchases vs sales aggregated by product
    You can extend this to include opening/closing stock, taxes, other costs.
    """
    start = timezone.datetime(year=year, month=1, day=1)
    end = timezone.datetime(year=year + 1, month=1, day=1)

    purchases = InventoryTransaction.objects.filter(transaction_type=InventoryTransaction.PURCHASE, created_at__gte=start, created_at__lt=end)
    sales = InventoryTransaction.objects.filter(transaction_type=InventoryTransaction.SALE, created_at__gte=start, created_at__lt=end)

    purchases_by_product = purchases.values('product').annotate(total_cost=Sum(ExpressionWrapper(F('unit_purchase_price') * F('quantity_boxes'), output_field=DecimalField(max_digits=18, decimal_places=6))))
    sales_by_product = sales.values('product').annotate(total_revenue=Sum(ExpressionWrapper(F('unit_sale_price') * F('quantity_boxes'), output_field=DecimalField(max_digits=18, decimal_places=6))))

    # join results into dict
    results = {}
    for p in purchases_by_product:
        results[p['product']] = {'total_cost': p['total_cost']}
    for s in sales_by_product:
        if s['product'] not in results:
            results[s['product']] = {}
        results[s['product']]['total_revenue'] = s['total_revenue']

    return results


class Expense(models.Model):
    """
    Daily clinic expenses tracking.
    Records all operational expenses like tea, electricity, salaries, etc.
    """
    EXPENSE_CATEGORIES = [
        ('UTILITIES', 'Utilities (Electric, Water, Gas)'),
        ('SALARIES', 'Staff Salaries'),
        ('SUPPLIES', 'Office Supplies'),
        ('MAINTENANCE', 'Maintenance & Repairs'),
        ('FOOD', 'Tea/Coffee/Food'),
        ('TRANSPORT', 'Transportation'),
        ('RENT', 'Rent'),
        ('MARKETING', 'Marketing & Advertising'),
        ('MISC', 'Miscellaneous'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, help_text='Brief description of expense')
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES, default='MISC')
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text='Amount in PKR')
    expense_date = models.DateField(default=timezone.now, help_text='Date of expense')
    notes = models.TextField(blank=True, null=True, help_text='Additional details')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'
    
    def __str__(self):
        return f"{self.title} - PKR {self.amount} ({self.expense_date})"


# Notes for integration:
# - Register Product and InventoryTransaction in admin to allow easy creation.
# - When creating InventoryTransaction, supply quantities in the granularity you have.
#   e.g., if you received 3 boxes, set quantity_boxes=3 and the system will update cached totals.
# - For more advanced per-item tracking (serial numbers), create a separate StockItem model.
# - For performance and concurrency, consider using database-level transactions and async
#   queueing (Celery) for heavy recalculations of cached stock totals.

# Example admin registration (put in admin.py):
# from django.contrib import admin
# from .models import Product, InventoryTransaction, ProductCategory, Expense
# admin.site.register(ProductCategory)
# admin.site.register(Product)
# admin.site.register(InventoryTransaction)
# admin.site.register(Expense)
