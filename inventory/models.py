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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True)

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

        # compute purchase price per item and per subitem
        # The purchase_price is for the TOTAL quantity (products_in_box packs)
        # So if user enters 10 packs and purchase_price = 4000, then price per pack = 4000/10 = 400
        try:
            # price per single pack/box
            price_per_pack = Decimal(self.purchase_price) / Decimal(self.products_in_box)
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
            # sale price for total quantity (same structure as purchase_price)
            self.sale_price = quantize_decimal(Decimal(self.purchase_price) * (Decimal('1') + margin), places=6)

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
        
        # Check if this is a new product (no pk yet)
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Initialize stock for new products by creating initial transaction
        if is_new and self.products_in_box > 0:
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

    def update_cached_stock(self):
        """Calculate totals from InventoryTransaction records and cache them on model."""
        aggregates = InventoryTransaction.objects.filter(product=self).aggregate(
            in_boxes=models.Sum('quantity_boxes'),
            out_boxes=models.Sum('quantity_boxes_out'),
            in_items=models.Sum('quantity_items'),
            out_items=models.Sum('quantity_items_out'),
            in_sub=models.Sum('quantity_subitems'),
            out_sub=models.Sum('quantity_subitems_out')
        )
        # For backward compat, if none exist, treat as zero
        in_boxes = aggregates.get('in_boxes') or Decimal('0')
        out_boxes = aggregates.get('out_boxes') or Decimal('0')
        in_items = aggregates.get('in_items') or Decimal('0')
        out_items = aggregates.get('out_items') or Decimal('0')
        in_sub = aggregates.get('in_sub') or Decimal('0')
        out_sub = aggregates.get('out_sub') or Decimal('0')

        # We'll prefer computing totals in the finest granularity (subitems) and derive others
        total_sub = in_sub - out_sub
        total_items = (in_items - out_items) or (total_sub / Decimal(self.subitems_per_item) if self.subitems_per_item else Decimal('0'))
        total_boxes = (in_boxes - out_boxes) or (total_items / Decimal(self.items_per_product) if self.items_per_product else Decimal('0'))

        self.total_boxes = quantize_decimal(total_boxes, places=6)
        self.total_items = quantize_decimal(total_items, places=6)
        self.total_subitems = quantize_decimal(total_sub, places=6)
        self.save(update_fields=['total_boxes', 'total_items', 'total_subitems'])

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
        if self.transaction_type in {self.OUTGOING, self.SALE}:
            self.quantity_boxes_out = self.quantity_boxes
            self.quantity_items_out = self.quantity_items
            self.quantity_subitems_out = self.quantity_subitems
        else:
            # incoming/purchase
            self.quantity_boxes_out = Decimal('0')
            self.quantity_items_out = Decimal('0')
            self.quantity_subitems_out = Decimal('0')

        super().save(*args, **kwargs)

        # Optionally update cached totals on product
        try:
            self.product.update_cached_stock()
        except Exception:
            # In heavy traffic environments you may want to queue this call
            pass

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
