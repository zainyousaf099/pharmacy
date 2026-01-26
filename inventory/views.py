# inventory/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from decimal import Decimal
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from datetime import datetime, timedelta
from io import BytesIO
import calendar
from django.http import JsonResponse, HttpResponse
import csv
from django.template.loader import get_template
from xhtml2pdf import pisa

from .models import Product, InventoryTransaction, ProductCategory, Expense, ProductBatch, Distributor, DistributorPayment, DistributorPurchase
from .forms import ProductForm, PurchaseForm, SaleForm, ExpenseForm, ProductBatchForm, DistributorForm, DistributorPaymentForm, DistributorPurchaseForm

def dashboard(request):
    """Dashboard showing inventory summary"""
    total_products = Product.objects.count()
    total_categories = ProductCategory.objects.count()
    low_stock_products = Product.objects.filter(total_boxes__lt=5).count()
    
    # Get medicines expiring in the next 6 months
    today = timezone.now().date()
    six_months_later = today + timedelta(days=180)
    expiring_soon = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lte=six_months_later,
        expiry_date__gte=today
    ).order_by('expiry_date')
    
    # Categorize by urgency
    one_month_later = today + timedelta(days=30)
    three_months_later = today + timedelta(days=90)
    
    expired_products = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lt=today
    ).count()
    
    expiring_critical = expiring_soon.filter(expiry_date__lte=one_month_later).count()  # Within 1 month
    expiring_warning = expiring_soon.filter(expiry_date__gt=one_month_later, expiry_date__lte=three_months_later).count()  # 1-3 months
    expiring_info = expiring_soon.filter(expiry_date__gt=three_months_later).count()  # 3-6 months
    
    recent_transactions = InventoryTransaction.objects.all().order_by('-created_at')[:10]
    
    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'low_stock_products': low_stock_products,
        'recent_transactions': recent_transactions,
        'expiring_soon': expiring_soon,
        'expired_products': expired_products,
        'expiring_critical': expiring_critical,
        'expiring_warning': expiring_warning,
        'expiring_info': expiring_info,
        'today': today,
    }
    return render(request, "inventory/dashboard.html", context)

def product_list(request):
    """Paginated product list with AJAX support for fast loading"""
    # Check if this is an AJAX request for data
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return product_list_ajax(request)
    
    # For initial page load, just render the template (data loaded via AJAX)
    return render(request, "inventory/product_list.html", {})


def product_list_ajax(request):
    """AJAX endpoint for paginated product data with search"""
    from django.core.paginator import Paginator
    import json
    
    # Get parameters
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    search = request.GET.get('search', '').strip()
    
    # Base queryset with only needed fields for performance
    products = Product.objects.only(
        'id', 'name', 'category', 'weight_or_quantity', 
        'total_boxes', 'total_items', 'total_subitems',
        'purchase_price', 'sale_price', 'batch_no'
    ).select_related('category')
    
    # Get stock statistics (before applying search filter)
    total_all = Product.objects.count()
    in_stock = Product.objects.filter(total_boxes__gt=0).count()
    out_of_stock = Product.objects.filter(total_boxes__lte=0).count()
    low_stock = Product.objects.filter(total_boxes__gt=0, total_boxes__lt=5).count()
    
    # Apply search filter
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(weight_or_quantity__icontains=search) |
            Q(batch_no__icontains=search)
        )
    
    # Order by name
    products = products.order_by('name')
    
    # Paginate
    paginator = Paginator(products, per_page)
    page_obj = paginator.get_page(page)
    
    # Build response data
    products_data = []
    for p in page_obj:
        products_data.append({
            'id': str(p.pk),
            'name': p.name,
            'batch_no': p.batch_no or '',
            'category': p.category.name if p.category else '',
            'dosage': p.weight_or_quantity or '',
            'total_boxes': int(p.total_boxes or 0),
            'total_items': int(p.total_items or 0),
            'total_subitems': int(p.total_subitems or 0),
            'purchase_price': float(p.purchase_price or 0),
            'sale_price': float(p.sale_price or 0),
        })
    
    return JsonResponse({
        'products': products_data,
        'page': page,
        'per_page': per_page,
        'total_pages': paginator.num_pages,
        'total_count': paginator.count,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'stats': {
            'total': total_all,
            'in_stock': in_stock,
            'out_of_stock': out_of_stock,
            'low_stock': low_stock,
        }
    })

def product_create(request):
    new_distributor_name = ''
    selected_distributor_id = ''
    
    if request.method == "POST":
        form = ProductForm(request.POST)
        
        # Get distributor values from POST to preserve them on form errors
        selected_distributor_id = request.POST.get('distributor_ref', '').strip()
        new_distributor_name = request.POST.get('new_distributor', '').strip()
        
        if form.is_valid():
            product = form.save(commit=False)
            
            if new_distributor_name:
                # Create new distributor if name provided
                distributor, created = Distributor.objects.get_or_create(
                    name__iexact=new_distributor_name,
                    defaults={'name': new_distributor_name}
                )
                product.distributor_ref = distributor
                product.distributor = new_distributor_name  # Keep legacy field updated
            elif selected_distributor_id and selected_distributor_id != '__new__':
                # Use selected existing distributor
                try:
                    distributor = Distributor.objects.get(pk=selected_distributor_id)
                    product.distributor_ref = distributor
                    product.distributor = distributor.name
                except Distributor.DoesNotExist:
                    pass
            
            # ensure required numeric defaults
            if product.products_in_box < 1: product.products_in_box = 1
            if product.items_per_product < 1: product.items_per_product = 1
            if product.subitems_per_item < 1: product.subitems_per_item = 1
            
            # Handle empty discount fields - set to 0 if not provided
            if product.distributor_discount_pkr is None:
                product.distributor_discount_pkr = Decimal('0.00')
            if product.distributor_discount_percent is None:
                product.distributor_discount_percent = Decimal('0.00')
            
            product.save()
            
            # Update distributor's total_purchases with the initial stock value
            if product.distributor_ref and product.products_in_box > 0:
                purchase_amount = product.net_purchase_price * product.products_in_box
                product.distributor_ref.total_purchases += purchase_amount
                product.distributor_ref.save(update_fields=['total_purchases'])
            
            messages.success(request, f"Product '{product.name}' created successfully! Price per Pack: Rs. {float(product.net_purchase_price):.2f}, per Strip: Rs. {float(product.purchase_price_per_item):.2f}, per Tablet: Rs. {float(product.purchase_price_per_subitem):.2f}")
            return redirect("inventory:product_list")
    else:
        form = ProductForm()
    
    distributors = Distributor.objects.all()
    return render(request, "inventory/product_create.html", {
        "form": form, 
        "distributors": distributors,
        "new_distributor_name": new_distributor_name,
        "selected_distributor_id": selected_distributor_id,
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    transactions = product.transactions.all().order_by('-created_at')[:50]
    batches = product.batches.filter(is_active=True).order_by('expiry_date')
    all_batches = product.batches.all().order_by('expiry_date')
    return render(request, "inventory/product_detail.html", {
        "product": product, 
        "transactions": transactions,
        "batches": batches,
        "all_batches": all_batches
    })

def add_purchase(request, pk):
    """
    Create a PURCHASE InventoryTransaction for product `pk`.
    The form expects quantity_boxes, quantity_items and quantity_subitems.
    The model's save() will call product.update_cached_stock() so cached totals update.
    """
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = PurchaseForm(request.POST)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.product = product
            txn.transaction_type = InventoryTransaction.PURCHASE
            # If user didn't set unit_purchase_price on form, use product's net_purchase_price (per pack)
            if not txn.unit_purchase_price or txn.unit_purchase_price == Decimal('0'):
                txn.unit_purchase_price = product.net_purchase_price
            txn.save()
            messages.success(request, "Purchase recorded and stock updated successfully!")
            return redirect("inventory:product_detail", pk=product.pk)
    else:
        initial = {
            "unit_purchase_price": product.net_purchase_price  # Price is already per pack
        }
        form = PurchaseForm(initial=initial)

    # helpful hints for user
    context = {
        "product": product,
        "form": form,
        "items_per_product": product.items_per_product,
        "subitems_per_item": product.subitems_per_item,
    }
    return render(request, "inventory/add_purchase.html", context)


def add_sale(request, pk):
    """Record a sale transaction with batch selection (FEFO)"""
    product = get_object_or_404(Product, pk=pk)
    
    # Get available batches ordered by expiry (FEFO)
    available_batches = ProductBatch.objects.filter(
        product=product,
        is_active=True,
        current_subitems__gt=0
    ).order_by('expiry_date', 'created_at')

    if request.method == "POST":
        form = SaleForm(request.POST)
        batch_id = request.POST.get('batch_id')
        
        if form.is_valid():
            txn = form.save(commit=False)
            txn.product = product
            txn.transaction_type = InventoryTransaction.SALE
            
            # Get selected batch if specified
            selected_batch = None
            if batch_id:
                try:
                    selected_batch = ProductBatch.objects.get(pk=batch_id, product=product)
                    txn.batch = selected_batch
                    # Use batch's sale price if available
                    if not txn.unit_sale_price or txn.unit_sale_price == Decimal('0'):
                        txn.unit_sale_price = selected_batch.sale_price_per_pack or product.sale_price or Decimal('0')
                except ProductBatch.DoesNotExist:
                    pass
            else:
                # Auto-select earliest expiry batch (FEFO)
                if available_batches.exists():
                    selected_batch = available_batches.first()
                    txn.batch = selected_batch
                    if not txn.unit_sale_price or txn.unit_sale_price == Decimal('0'):
                        txn.unit_sale_price = selected_batch.sale_price_per_pack or product.sale_price or Decimal('0')
                elif not txn.unit_sale_price or txn.unit_sale_price == Decimal('0'):
                    txn.unit_sale_price = product.sale_price if product.sale_price else Decimal('0')
            
            txn.save()
            
            # Update batch stock if batch was selected
            if selected_batch:
                selected_batch.update_stock()
            
            batch_info = f" from Batch: {selected_batch.batch_no or 'N/A'}" if selected_batch else ""
            messages.success(request, f"Sale recorded successfully{batch_info}!")
            return redirect("inventory:product_detail", pk=product.pk)
    else:
        # Pre-select earliest expiry batch price
        initial_price = product.sale_price or Decimal('0')
        suggested_batch = None
        if available_batches.exists():
            suggested_batch = available_batches.first()
            if suggested_batch.sale_price_per_pack:
                initial_price = suggested_batch.sale_price_per_pack
        
        initial = {
            "unit_sale_price": initial_price
        }
        form = SaleForm(initial=initial)

    context = {
        "product": product,
        "form": form,
        "items_per_product": product.items_per_product,
        "subitems_per_item": product.subitems_per_item,
        "available_batches": available_batches,
        "suggested_batch": available_batches.first() if available_batches.exists() else None,
    }
    return render(request, "inventory/add_sale.html", context)


def add_batch(request, pk):
    """Add a new batch to an existing product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == "POST":
        form = ProductBatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.product = product
            
            # Handle new distributor creation
            new_distributor_name = request.POST.get('new_distributor', '').strip()
            if new_distributor_name:
                distributor, created = Distributor.objects.get_or_create(
                    name__iexact=new_distributor_name,
                    defaults={'name': new_distributor_name}
                )
                batch.distributor = distributor
            
            # Copy sale price from product if not provided
            if not batch.sale_price_per_pack:
                batch.sale_price_per_pack = product.sale_price
            batch.save()
            
            # Update distributor's total_purchases
            if batch.distributor:
                purchase_amount = batch.net_purchase_price_per_pack * batch.quantity_packs
                batch.distributor.total_purchases += purchase_amount
                batch.distributor.save(update_fields=['total_purchases'])
            
            messages.success(request, f"New batch added for '{product.name}'! Batch: {batch.batch_no or 'N/A'}, Expiry: {batch.expiry_date or 'N/A'}")
            return redirect("inventory:product_detail", pk=product.pk)
    else:
        # Pre-fill with product's current prices and distributor
        initial = {
            "purchase_price_per_pack": product.purchase_price,
            "sale_price_per_pack": product.sale_price,
            "received_date": timezone.now().date(),
            "distributor": product.distributor_ref,  # Default to product's distributor
        }
        form = ProductBatchForm(initial=initial)
    
    distributors = Distributor.objects.all()
    context = {
        "product": product,
        "form": form,
        "distributors": distributors,
    }
    return render(request, "inventory/add_batch.html", context)


def batch_list(request):
    """List all batches, with filtering options"""
    batches = ProductBatch.objects.select_related('product').order_by('expiry_date')
    
    # Filter by status
    status = request.GET.get('status', 'active')
    if status == 'active':
        batches = batches.filter(is_active=True)
    elif status == 'expired':
        batches = batches.filter(expiry_date__lt=timezone.now().date())
    elif status == 'expiring':
        three_months = timezone.now().date() + timedelta(days=90)
        batches = batches.filter(
            expiry_date__isnull=False,
            expiry_date__gte=timezone.now().date(),
            expiry_date__lte=three_months
        )
    
    context = {
        "batches": batches,
        "status": status,
    }
    return render(request, "inventory/batch_list.html", context)


def batch_detail(request, pk):
    """View batch details and transactions"""
    batch = get_object_or_404(ProductBatch, pk=pk)
    transactions = batch.transactions.all().order_by('-created_at')
    
    context = {
        "batch": batch,
        "transactions": transactions,
    }
    return render(request, "inventory/batch_detail.html", context)


def reports(request):
    """Sales, Purchase, and Expense Reports"""
    # Get date filter from request
    period = request.GET.get('period', 'month')  # week, month, year, custom
    
    today = timezone.now()
    custom_start = None
    custom_end = None
    
    if period == 'custom':
        # Handle custom date range
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
            title = "Custom Range Report"
            custom_start = start_date_str
            custom_end = end_date_str
        else:
            # Fallback to month if custom dates not provided
            start_date = datetime(today.year, today.month, 1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = datetime(today.year, today.month, last_day, 23, 59, 59)
            title = "Monthly Report"
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())  # Start of week (Monday)
        end_date = start_date + timedelta(days=7)
        title = "Weekly Report"
    elif period == 'year':
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31, 23, 59, 59)
        title = "Yearly Report"
    else:  # month (default)
        start_date = datetime(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = datetime(today.year, today.month, last_day, 23, 59, 59)
        title = "Monthly Report"
    
    # Sales data
    sales = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(
        total_sales=Sum(F('quantity_boxes') * F('unit_sale_price')),
        total_quantity=Sum('quantity_boxes')
    )
    
    # Returns data
    returns = InventoryTransaction.objects.filter(
        transaction_type='RET',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(
        total_returns=Sum(F('quantity_subitems') * F('unit_sale_price')),
        total_quantity=Sum('quantity_subitems')
    )
    
    # Purchase data
    purchases = InventoryTransaction.objects.filter(
        transaction_type='PUR',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(
        total_purchases=Sum(F('quantity_boxes') * F('unit_purchase_price')),
        total_quantity=Sum('quantity_boxes')
    )
    
    # Expenses data
    expenses = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).aggregate(
        total_expenses=Sum('amount')
    )
    
    # Calculate profit/loss (deduct returns from sales)
    total_sales_raw = sales.get('total_sales') or Decimal('0')
    total_returns = returns.get('total_returns') or Decimal('0')
    total_sales = total_sales_raw - total_returns  # Net sales after returns
    total_purchases = purchases.get('total_purchases') or Decimal('0')
    total_expenses = expenses.get('total_expenses') or Decimal('0')
    profit_loss = total_sales - total_purchases - total_expenses
    
    # All returns transactions (for detailed view)
    all_returns = InventoryTransaction.objects.filter(
        transaction_type='RET',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related('product').order_by('-created_at')
    
    # Top selling products
    top_products = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).values('product__name').annotate(
        total_sold=Sum('quantity_boxes'),
        revenue=Sum(F('quantity_boxes') * F('unit_sale_price'))
    ).order_by('-total_sold')[:10]
    
    # Recent transactions
    recent_sales = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related('product').order_by('-created_at')[:10]
    
    recent_purchases = InventoryTransaction.objects.filter(
        transaction_type='PUR',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related('product').order_by('-created_at')[:10]
    
    # All sales transactions (for detailed view)
    all_sales = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related('product').order_by('-created_at')
    
    # All purchase transactions (for detailed view)
    all_purchases = InventoryTransaction.objects.filter(
        transaction_type='PUR',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related('product').order_by('-created_at')
    
    # Medicine-wise stock movement summary
    medicine_movements = InventoryTransaction.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    ).values('product__name').annotate(
        total_sales=Sum('quantity_boxes', filter=Q(transaction_type='SALE')),
        total_purchases=Sum('quantity_boxes', filter=Q(transaction_type='PUR')),
        sales_revenue=Sum(F('quantity_boxes') * F('unit_sale_price'), filter=Q(transaction_type='SALE')),
        purchase_cost=Sum(F('quantity_boxes') * F('unit_purchase_price'), filter=Q(transaction_type='PUR'))
    ).order_by('-total_sales')
    
    # Expenses by category
    expenses_by_category = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    context = {
        'period': period,
        'title': title,
        'start_date': start_date,
        'end_date': end_date,
        'custom_start': custom_start,
        'custom_end': custom_end,
        'total_sales': total_sales,
        'total_sales_raw': total_sales_raw,
        'total_returns': total_returns,
        'returns_quantity': returns.get('total_quantity') or 0,
        'total_purchases': total_purchases,
        'total_expenses': total_expenses,
        'profit_loss': profit_loss,
        'sales_quantity': sales.get('total_quantity') or 0,
        'purchase_quantity': purchases.get('total_quantity') or 0,
        'top_products': top_products,
        'recent_sales': recent_sales,
        'recent_purchases': recent_purchases,
        'all_sales': all_sales,
        'all_purchases': all_purchases,
        'all_returns': all_returns,
        'medicine_movements': medicine_movements,
        'expenses_by_category': expenses_by_category,
    }
    
    return render(request, "inventory/reports.html", context)


def expense_list(request):
    """List all expenses"""
    expenses = Expense.objects.all().order_by('-expense_date', '-created_at')
    
    # Calculate total expenses for current month
    today = timezone.now()
    month_start = datetime(today.year, today.month, 1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    month_end = datetime(today.year, today.month, last_day, 23, 59, 59)
    
    monthly_total = Expense.objects.filter(
        expense_date__gte=month_start.date(),
        expense_date__lte=month_end.date()
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    context = {
        'expenses': expenses[:50],  # Last 50 expenses
        'monthly_total': monthly_total,
    }
    return render(request, "inventory/expense_list.html", context)


def expense_create(request):
    """Add new expense"""
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save()
            messages.success(request, f"Expense '{expense.title}' added successfully!")
            return redirect("inventory:expense_list")
    else:
        form = ExpenseForm()
    
    return render(request, "inventory/expense_create.html", {"form": form})


# ==================== DISTRIBUTOR VIEWS ====================

def distributor_list(request):
    """List all distributors with their balances"""
    distributors = Distributor.objects.all().order_by('name')
    
    # Calculate totals
    total_purchases = distributors.aggregate(total=Sum('total_purchases'))['total'] or Decimal('0')
    total_paid = distributors.aggregate(total=Sum('total_paid'))['total'] or Decimal('0')
    total_due = total_purchases - total_paid
    
    # Filter by status
    status = request.GET.get('status', 'all')
    if status == 'due':
        distributors = [d for d in distributors if d.balance_due > 0]
    elif status == 'paid':
        distributors = [d for d in distributors if d.balance_due <= 0]
    
    context = {
        'distributors': distributors,
        'total_purchases': total_purchases,
        'total_paid': total_paid,
        'total_due': total_due,
        'status_filter': status,
    }
    return render(request, "inventory/distributor_list.html", context)


def distributor_create(request):
    """Create a new distributor"""
    if request.method == "POST":
        form = DistributorForm(request.POST)
        if form.is_valid():
            distributor = form.save()
            messages.success(request, f"Distributor '{distributor.name}' created successfully!")
            return redirect("inventory:distributor_list")
    else:
        form = DistributorForm()
    
    return render(request, "inventory/distributor_form.html", {"form": form, "title": "Add New Distributor"})


def distributor_detail(request, pk):
    """View distributor details, purchases, and payments"""
    distributor = get_object_or_404(Distributor, pk=pk)
    
    # Get purchases from this distributor (via batches)
    batches = ProductBatch.objects.filter(distributor=distributor).select_related('product').order_by('-received_date')
    
    # Get payments to this distributor
    payments = DistributorPayment.objects.filter(distributor=distributor).order_by('-payment_date')
    
    # Get purchase invoices
    purchases = DistributorPurchase.objects.filter(distributor=distributor).order_by('-invoice_date')
    
    # Products from this distributor
    products = Product.objects.filter(distributor_ref=distributor)
    
    context = {
        'distributor': distributor,
        'batches': batches[:20],
        'payments': payments[:20],
        'purchases': purchases[:20],
        'products': products,
    }
    return render(request, "inventory/distributor_detail.html", context)


def distributor_edit(request, pk):
    """Edit a distributor"""
    distributor = get_object_or_404(Distributor, pk=pk)
    
    if request.method == "POST":
        form = DistributorForm(request.POST, instance=distributor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Distributor '{distributor.name}' updated successfully!")
            return redirect("inventory:distributor_detail", pk=pk)
    else:
        form = DistributorForm(instance=distributor)
    
    return render(request, "inventory/distributor_form.html", {"form": form, "title": "Edit Distributor", "distributor": distributor})


def distributor_add_payment(request, pk):
    """Add a payment to a distributor"""
    distributor = get_object_or_404(Distributor, pk=pk)
    
    if request.method == "POST":
        form = DistributorPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.distributor = distributor
            payment.save()
            messages.success(request, f"Payment of Rs. {payment.amount} recorded for '{distributor.name}'!")
            return redirect("inventory:distributor_detail", pk=pk)
    else:
        form = DistributorPaymentForm(initial={
            'distributor': distributor,
            'payment_date': timezone.now().date()
        })
    
    context = {
        'form': form,
        'distributor': distributor,
    }
    return render(request, "inventory/distributor_add_payment.html", context)


def distributor_add_purchase(request, pk):
    """Add a purchase invoice from a distributor"""
    distributor = get_object_or_404(Distributor, pk=pk)
    
    if request.method == "POST":
        form = DistributorPurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.distributor = distributor
            purchase.save()
            messages.success(request, f"Purchase invoice Rs. {purchase.net_amount} recorded for '{distributor.name}'!")
            return redirect("inventory:distributor_detail", pk=pk)
    else:
        form = DistributorPurchaseForm(initial={
            'distributor': distributor,
            'invoice_date': timezone.now().date()
        })
    
    context = {
        'form': form,
        'distributor': distributor,
    }
    return render(request, "inventory/distributor_add_purchase.html", context)


def distributor_api(request):
    """API to get distributors for AJAX"""
    distributors = Distributor.objects.all().values('id', 'name', 'phone', 'balance_due')
    return JsonResponse(list(distributors), safe=False)


def distributor_dues_report(request):
    """Report showing all distributor dues"""
    distributors = Distributor.objects.all().order_by('name')
    
    # Get distributors with dues
    distributors_with_dues = [d for d in distributors if d.balance_due > 0]
    
    # Calculate totals
    total_due = sum(d.balance_due for d in distributors_with_dues)
    
    # Recent payments
    recent_payments = DistributorPayment.objects.all().order_by('-payment_date')[:20]
    
    context = {
        'distributors': distributors_with_dues,
        'total_due': total_due,
        'recent_payments': recent_payments,
    }
    return render(request, "inventory/distributor_dues_report.html", context)


def expense_reports(request):
    """Expense Reports - Daily, Weekly, Monthly, and Yearly"""
    # Get date filter from request
    period = request.GET.get('period', 'day')  # day, week, month, year
    
    today = timezone.now()
    
    if period == 'day':
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59)
        title = "Daily Expense Report"
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())  # Start of week (Monday)
        end_date = start_date + timedelta(days=7)
        title = "Weekly Expense Report"
    elif period == 'year':
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31, 23, 59, 59)
        title = "Yearly Expense Report"
    else:  # month
        start_date = datetime(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = datetime(today.year, today.month, last_day, 23, 59, 59)
        title = "Monthly Expense Report"
    
    # Total expenses for the period
    total_expenses = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Count of expenses
    expense_count = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).count()
    
    # Expenses by category
    expenses_by_category = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Recent expenses in the period
    recent_expenses = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).order_by('-expense_date', '-created_at')
    
    # Top 10 highest expenses
    top_expenses = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).order_by('-amount')[:10]
    
    # Calculate average expense
    average_expense = total_expenses / expense_count if expense_count > 0 else Decimal('0')
    
    # Daily expenses breakdown (for week and month)
    daily_expenses = []
    if period in ['week', 'month']:
        daily_expenses = Expense.objects.filter(
            expense_date__gte=start_date.date(),
            expense_date__lte=end_date.date()
        ).values('expense_date').annotate(
            daily_total=Sum('amount'),
            daily_count=Count('id')
        ).order_by('expense_date')
    
    # For daily view, get hourly breakdown (by expense entry time)
    hourly_expenses = []
    if period == 'day':
        hourly_expenses = recent_expenses  # Show all today's expenses in detail
    
    context = {
        'period': period,
        'title': title,
        'start_date': start_date,
        'end_date': end_date,
        'total_expenses': total_expenses,
        'expense_count': expense_count,
        'average_expense': average_expense,
        'expenses_by_category': expenses_by_category,
        'recent_expenses': recent_expenses,
        'top_expenses': top_expenses,
        'daily_expenses': daily_expenses,
        'hourly_expenses': hourly_expenses,
        'today': today,
    }
    
    return render(request, "inventory/expense_reports.html", context)


def expense_reports_csv(request):
    """Download Expense Reports as CSV"""
    period = request.GET.get('period', 'month')
    
    today = timezone.now()
    
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
        title = "Weekly_Expense_Report"
    elif period == 'year':
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31, 23, 59, 59)
        title = "Yearly_Expense_Report"
    else:
        start_date = datetime(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = datetime(today.year, today.month, last_day, 23, 59, 59)
        title = "Monthly_Expense_Report"
    
    # Get expenses
    expenses = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).order_by('-expense_date', '-created_at')
    
    # Calculate totals
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    expense_count = expenses.count()
    average_expense = total_expenses / expense_count if expense_count > 0 else Decimal('0')
    
    # Expenses by category
    expenses_by_category = expenses.values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Create CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{title}_{today.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow([f'{title.replace("_", " ")}'])
    writer.writerow([f'Period: {start_date.strftime("%B %d, %Y")} - {end_date.strftime("%B %d, %Y")}'])
    writer.writerow([f'Generated: {today.strftime("%B %d, %Y %I:%M %p")}'])
    writer.writerow([])
    
    # Summary
    writer.writerow(['SUMMARY'])
    writer.writerow(['Total Expenses', f'PKR {total_expenses:,.2f}'])
    writer.writerow(['Number of Transactions', expense_count])
    writer.writerow(['Average Expense', f'PKR {average_expense:,.2f}'])
    writer.writerow([])
    
    # Expenses by Category
    writer.writerow(['EXPENSES BY CATEGORY'])
    writer.writerow(['Category', 'Amount (PKR)', 'Count', 'Percentage'])
    for cat in expenses_by_category:
        percentage = (float(cat['total']) / float(total_expenses) * 100) if total_expenses > 0 else 0
        writer.writerow([
            cat['category'],
            f'{cat["total"]:,.2f}',
            cat['count'],
            f'{percentage:.1f}%'
        ])
    writer.writerow([])
    
    # All Expenses Details
    writer.writerow(['ALL EXPENSES'])
    writer.writerow(['Date', 'Title', 'Category', 'Amount (PKR)', 'Notes'])
    for expense in expenses:
        writer.writerow([
            expense.expense_date.strftime('%Y-%m-%d'),
            expense.title,
            expense.get_category_display(),
            f'{expense.amount:,.2f}',
            expense.notes or ''
        ])
    
    return response


def expense_reports_pdf(request):
    """Download Expense Reports as PDF"""
    period = request.GET.get('period', 'month')
    
    today = timezone.now()
    
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
        title = "Weekly Expense Report"
    elif period == 'year':
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31, 23, 59, 59)
        title = "Yearly Expense Report"
    else:
        start_date = datetime(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = datetime(today.year, today.month, last_day, 23, 59, 59)
        title = "Monthly Expense Report"
    
    # Get all data
    total_expenses = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    expense_count = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).count()
    
    expenses_by_category = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    recent_expenses = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).order_by('-expense_date', '-created_at')
    
    top_expenses = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).order_by('-amount')[:10]
    
    average_expense = total_expenses / expense_count if expense_count > 0 else Decimal('0')
    
    context = {
        'period': period,
        'title': title,
        'start_date': start_date,
        'end_date': end_date,
        'total_expenses': total_expenses,
        'expense_count': expense_count,
        'average_expense': average_expense,
        'expenses_by_category': expenses_by_category,
        'recent_expenses': recent_expenses,
        'top_expenses': top_expenses,
        'today': today,
    }
    
    # Render template
    template = get_template('inventory/expense_reports_pdf.html')
    html = template.render(context)
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Expense_Report_{period}_{today.strftime("%Y%m%d")}.pdf"'
    
    # Generate PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    return response


def product_update(request, pk):
    """Update product details and prices"""
    product = get_object_or_404(Product, pk=pk)
    new_distributor_name = ''
    selected_distributor_id = ''
    
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        
        # Get distributor values from POST to preserve them on form errors
        selected_distributor_id = request.POST.get('distributor_ref', '').strip()
        new_distributor_name = request.POST.get('new_distributor', '').strip()
        
        if form.is_valid():
            updated_product = form.save(commit=False)
            
            if new_distributor_name:
                # Create new distributor if name provided
                distributor, created = Distributor.objects.get_or_create(
                    name__iexact=new_distributor_name,
                    defaults={'name': new_distributor_name}
                )
                updated_product.distributor_ref = distributor
                updated_product.distributor = new_distributor_name
            elif selected_distributor_id and selected_distributor_id != '__new__':
                # Use selected existing distributor
                try:
                    distributor = Distributor.objects.get(pk=selected_distributor_id)
                    updated_product.distributor_ref = distributor
                    updated_product.distributor = distributor.name
                except Distributor.DoesNotExist:
                    pass
            elif selected_distributor_id == '':
                # Clear distributor if none selected
                updated_product.distributor_ref = None
                updated_product.distributor = ''
            
            # ensure required numeric defaults
            if updated_product.products_in_box < 1: updated_product.products_in_box = 1
            if updated_product.items_per_product < 1: updated_product.items_per_product = 1
            if updated_product.subitems_per_item < 1: updated_product.subitems_per_item = 1
            
            # Handle empty discount fields - set to 0 if not provided
            if updated_product.distributor_discount_pkr is None:
                updated_product.distributor_discount_pkr = Decimal('0.00')
            if updated_product.distributor_discount_percent is None:
                updated_product.distributor_discount_percent = Decimal('0.00')
            
            updated_product.save()
            messages.success(request, f"Product '{updated_product.name}' updated successfully!")
            return redirect("inventory:product_detail", pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    distributors = Distributor.objects.all()
    context = {
        "form": form,
        "product": product,
        "is_update": True,
        "distributors": distributors,
        "new_distributor_name": new_distributor_name,
        "selected_distributor_id": selected_distributor_id,
    }
    return render(request, "inventory/product_create.html", context)


def search_products_api(request):
    """API endpoint for product search autocomplete"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'results': []})
    
    # Search by name (case-insensitive, starts with or contains)
    products = Product.objects.filter(
        Q(name__istartswith=query) | Q(name__icontains=query)
    ).order_by('name')[:10]  # Limit to 10 results
    
    results = []
    for product in products:
        results.append({
            'id': str(product.id),
            'name': product.name,
            'category': product.category.name if product.category else '',
            'stock': float(product.current_stock_boxes),
            'url': reverse('inventory:product_detail', kwargs={'pk': product.pk})
        })
    
    return JsonResponse({'results': results})


def product_detail_api(request, product_id):
    """API endpoint to get product details by ID"""
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse({
            'success': True,
            'product': {
                'id': str(product.id),
                'name': product.name,
                'category': product.category.name if product.category else '',
                'total_items': float(product.total_items),
                'sale_price_per_subitem': float(product.sale_price_per_subitem) if product.sale_price_per_subitem else 0,
                'purchase_price_per_subitem': float(product.purchase_price_per_subitem) if product.purchase_price_per_subitem else 0,
                'weight_or_quantity': product.weight_or_quantity or '',
                'expiry_date': product.expiry_date.strftime('%Y-%m-%d') if product.expiry_date else None
            }
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)


def reports_csv(request):
    """Download sales/purchase reports as CSV"""
    import csv
    from django.http import HttpResponse
    
    period = request.GET.get('period', 'month')
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    
    today = timezone.now()
    
    # Determine date range
    if period == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
        title = "Weekly Report"
    elif period == 'year':
        start_date = today - timedelta(days=365)
        end_date = today
        title = "Yearly Report"
    elif period == 'custom' and start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        title = f"Custom Report ({start_date_str} to {end_date_str})"
    else:  # default to month
        start_date = today - timedelta(days=30)
        end_date = today
        title = "Monthly Report"
    
    # Query data
    sales = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(
        total_amount=Sum(F('quantity_boxes') * F('unit_sale_price')),
        total_quantity=Sum('quantity_boxes')
    )
    
    purchases = InventoryTransaction.objects.filter(
        transaction_type='PUR',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(
        total_amount=Sum(F('quantity_boxes') * F('unit_purchase_price')),
        total_quantity=Sum('quantity_boxes')
    )
    
    expenses = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).aggregate(total=Sum('amount'))
    
    total_sales = sales.get('total_amount') or Decimal('0')
    total_purchases = purchases.get('total_amount') or Decimal('0')
    total_expenses = expenses.get('total') or Decimal('0')
    profit_loss = total_sales - total_purchases - total_expenses
    
    # Get all transactions
    all_sales = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related('product').order_by('-created_at')
    
    all_purchases = InventoryTransaction.objects.filter(
        transaction_type='PUR',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related('product').order_by('-created_at')
    
    all_expenses = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).order_by('-expense_date')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="inventory_report_{period}_{today.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Summary Section
    writer.writerow([title])
    writer.writerow([f'Period: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}'])
    writer.writerow([])
    writer.writerow(['SUMMARY'])
    writer.writerow(['Total Sales', f'Rs. {total_sales:,.2f}'])
    writer.writerow(['Total Purchases', f'Rs. {total_purchases:,.2f}'])
    writer.writerow(['Total Expenses', f'Rs. {total_expenses:,.2f}'])
    writer.writerow(['Profit/Loss', f'Rs. {profit_loss:,.2f}'])
    writer.writerow(['Sales Quantity', f'{sales.get("total_quantity") or 0} boxes'])
    writer.writerow(['Purchase Quantity', f'{purchases.get("total_quantity") or 0} boxes'])
    writer.writerow([])
    
    # Sales Details
    writer.writerow(['SALES TRANSACTIONS'])
    writer.writerow(['Date', 'Medicine', 'Quantity', 'Unit Price', 'Total Amount'])
    for sale in all_sales:
        total = sale.quantity_boxes * sale.unit_sale_price
        writer.writerow([
            sale.created_at.strftime('%Y-%m-%d %H:%M'),
            sale.product.name,
            f'{sale.quantity_boxes} boxes',
            f'Rs. {sale.unit_sale_price:,.2f}',
            f'Rs. {total:,.2f}'
        ])
    writer.writerow([])
    
    # Purchase Details
    writer.writerow(['PURCHASE TRANSACTIONS'])
    writer.writerow(['Date', 'Medicine', 'Quantity', 'Unit Price', 'Total Amount'])
    for purchase in all_purchases:
        total = purchase.quantity_boxes * purchase.unit_purchase_price
        writer.writerow([
            purchase.created_at.strftime('%Y-%m-%d %H:%M'),
            purchase.product.name,
            f'{purchase.quantity_boxes} boxes',
            f'Rs. {purchase.unit_purchase_price:,.2f}',
            f'Rs. {total:,.2f}'
        ])
    writer.writerow([])
    
    # Expenses Details
    writer.writerow(['EXPENSES'])
    writer.writerow(['Date', 'Title', 'Category', 'Amount', 'Notes'])
    for expense in all_expenses:
        writer.writerow([
            expense.expense_date.strftime('%Y-%m-%d'),
            expense.title,
            expense.category,
            f'Rs. {expense.amount:,.2f}',
            expense.notes or ''
        ])
    
    return response


def reports_pdf(request):
    """Download sales/purchase reports as PDF"""
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from io import BytesIO
    
    period = request.GET.get('period', 'month')
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    
    today = timezone.now()
    
    # Determine date range
    if period == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
        title = "Weekly Report"
    elif period == 'year':
        start_date = today - timedelta(days=365)
        end_date = today
        title = "Yearly Report"
    elif period == 'custom' and start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        title = f"Custom Report ({start_date_str} to {end_date_str})"
    else:  # default to month
        start_date = today - timedelta(days=30)
        end_date = today
        title = "Monthly Report"
    
    # Query data (same as CSV)
    sales = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(
        total_amount=Sum(F('quantity_boxes') * F('unit_sale_price')),
        total_quantity=Sum('quantity_boxes')
    )
    
    # Returns data
    returns = InventoryTransaction.objects.filter(
        transaction_type='RET',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(
        total_amount=Sum(F('quantity_subitems') * F('unit_sale_price')),
        total_quantity=Sum('quantity_subitems')
    )
    
    purchases = InventoryTransaction.objects.filter(
        transaction_type='PUR',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(
        total_amount=Sum(F('quantity_boxes') * F('unit_purchase_price')),
        total_quantity=Sum('quantity_boxes')
    )
    
    expenses = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).aggregate(total=Sum('amount'))
    
    total_sales_raw = sales.get('total_amount') or Decimal('0')
    total_returns = returns.get('total_amount') or Decimal('0')
    total_sales = total_sales_raw - total_returns  # Net sales
    total_purchases = purchases.get('total_amount') or Decimal('0')
    total_expenses = expenses.get('total') or Decimal('0')
    profit_loss = total_sales - total_purchases - total_expenses
    
    # Get all transactions
    all_sales = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related('product').order_by('-created_at')
    
    all_purchases = InventoryTransaction.objects.filter(
        transaction_type='PUR',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related('product').order_by('-created_at')
    
    all_returns = InventoryTransaction.objects.filter(
        transaction_type='RET',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related('product').order_by('-created_at')
    
    all_expenses = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).order_by('-expense_date')
    
    context = {
        'title': title,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_sales_raw': total_sales_raw,
        'total_returns': total_returns,
        'returns_quantity': returns.get('total_quantity') or 0,
        'total_purchases': total_purchases,
        'total_expenses': total_expenses,
        'profit_loss': profit_loss,
        'sales_quantity': sales.get('total_quantity') or 0,
        'purchase_quantity': purchases.get('total_quantity') or 0,
        'all_sales': all_sales,
        'all_purchases': all_purchases,
        'all_returns': all_returns,
        'all_expenses': all_expenses,
    }
    
    template = get_template('inventory/reports_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="inventory_report_{period}_{today.strftime("%Y%m%d")}.pdf"'
    
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    return response


# ============ COMPREHENSIVE REPORTS ============

def all_reports(request):
    """Main reports hub page with all report types"""
    today = timezone.now().date()
    
    # Quick stats for the dashboard
    total_products = Product.objects.count()
    low_stock_count = Product.objects.filter(total_boxes__lt=5).count()
    
    # Expiring products
    thirty_days = today + timedelta(days=30)
    expiring_soon = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lte=thirty_days,
        expiry_date__gte=today
    ).count()
    
    expired = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lt=today
    ).count()
    
    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'expiring_soon': expiring_soon,
        'expired': expired,
    }
    return render(request, "inventory/all_reports.html", context)


def medicine_report(request, pk):
    """Detailed report for a single medicine"""
    product = get_object_or_404(Product, pk=pk)
    
    # Get date range from request or default to all time
    period = request.GET.get('period', 'all')
    today = timezone.now()
    
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = None
    
    # Get all transactions for this product
    transactions = product.transactions.all().order_by('-created_at')
    
    if start_date:
        transactions = transactions.filter(created_at__gte=start_date)
    
    # Calculate statistics
    sales = transactions.filter(transaction_type='SALE')
    purchases = transactions.filter(transaction_type='PUR')
    
    # For sales, use quantity_subitems_out (tablets sold)
    total_sales_qty = sales.aggregate(total=Sum('quantity_subitems_out'))['total'] or 0
    total_sales_amount = sales.aggregate(
        total=Sum(F('quantity_subitems_out') * F('unit_sale_price'))
    )['total'] or Decimal('0')
    
    # For purchases, use quantity_boxes (packs purchased)
    total_purchases_qty = purchases.aggregate(total=Sum('quantity_boxes'))['total'] or 0
    total_purchases_amount = purchases.aggregate(
        total=Sum(F('quantity_boxes') * F('unit_purchase_price'))
    )['total'] or Decimal('0')
    
    # Calculate cost of goods sold (using purchase price per subitem for sold tablets)
    cost_of_goods_sold = sales.aggregate(
        total=Sum(F('quantity_subitems_out') * F('unit_purchase_price'))
    )['total'] or Decimal('0')
    
    # Profit from this medicine
    profit = total_sales_amount - cost_of_goods_sold
    
    # Calculate profit margin percentage
    if total_sales_amount > 0:
        profit_margin = (profit / total_sales_amount) * 100
    else:
        profit_margin = Decimal('0')
    
    context = {
        'product': product,
        'transactions': transactions[:50],
        'sales': sales[:20],
        'purchases': purchases[:20],
        'total_sales_qty': total_sales_qty,
        'total_sales_amount': total_sales_amount,
        'total_purchases_qty': total_purchases_qty,
        'total_purchases_amount': total_purchases_amount,
        'profit': profit,
        'profit_margin': profit_margin,
        'period': period,
    }
    return render(request, "inventory/medicine_report.html", context)


def medicine_report_pdf(request, pk):
    """PDF report for a single medicine"""
    product = get_object_or_404(Product, pk=pk)
    today = timezone.now()
    
    # Get all transactions
    transactions = product.transactions.all().order_by('-created_at')[:100]
    sales = product.transactions.filter(transaction_type='SALE')
    purchases = product.transactions.filter(transaction_type='PUR')
    
    # For sales, use quantity_subitems_out (tablets sold)
    total_sales_qty = sales.aggregate(total=Sum('quantity_subitems_out'))['total'] or 0
    total_sales_amount = sales.aggregate(
        total=Sum(F('quantity_subitems_out') * F('unit_sale_price'))
    )['total'] or Decimal('0')
    
    # For purchases, use quantity_boxes (packs purchased)
    total_purchases_qty = purchases.aggregate(total=Sum('quantity_boxes'))['total'] or 0
    total_purchases_amount = purchases.aggregate(
        total=Sum(F('quantity_boxes') * F('unit_purchase_price'))
    )['total'] or Decimal('0')
    
    # Cost of goods sold
    cost_of_goods_sold = sales.aggregate(
        total=Sum(F('quantity_subitems_out') * F('unit_purchase_price'))
    )['total'] or Decimal('0')
    
    profit = total_sales_amount - cost_of_goods_sold
    
    context = {
        'product': product,
        'transactions': transactions,
        'total_sales_qty': total_sales_qty,
        'total_sales_amount': total_sales_amount,
        'total_purchases_qty': total_purchases_qty,
        'total_purchases_amount': total_purchases_amount,
        'profit': profit,
        'generated_at': today,
    }
    
    template = get_template('inventory/medicine_report_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="medicine_report_{product.name}_{today.strftime("%Y%m%d")}.pdf"'
    
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    return response


def stock_report(request):
    """Complete stock report - all medicines with stock levels and batch breakdown"""
    products = Product.objects.all().order_by('name')
    
    # Calculate total stock value
    total_purchase_value = Decimal('0')
    total_sale_value = Decimal('0')
    
    for product in products:
        stock_boxes = product.total_boxes or 0
        if stock_boxes > 0:
            # Calculate stock value for each product
            product.stock_value = Decimal(stock_boxes) * Decimal(product.purchase_price or 0)
            total_purchase_value += product.stock_value
            total_sale_value += Decimal(stock_boxes) * Decimal(product.sale_price or 0)
        else:
            product.stock_value = Decimal('0')
        
        # Add batch information
        product.active_batches = product.batches.filter(is_active=True, current_subitems__gt=0).order_by('expiry_date')
        product.batch_count = product.active_batches.count()
    
    # Get batch-level totals
    all_batches = ProductBatch.objects.filter(is_active=True).select_related('product')
    batch_purchase_value = sum(
        (b.current_packs * b.net_purchase_price_per_pack) for b in all_batches
    )
    batch_sale_value = sum(
        (b.current_packs * (b.sale_price_per_pack or b.product.sale_price or Decimal('0'))) for b in all_batches
    )
    
    context = {
        'products': products,
        'total_products': products.count(),
        'total_purchase_value': total_purchase_value,
        'total_sale_value': total_sale_value,
        'potential_profit': total_sale_value - total_purchase_value,
        'batch_purchase_value': batch_purchase_value,
        'batch_sale_value': batch_sale_value,
        'batch_potential_profit': batch_sale_value - batch_purchase_value,
        'total_batches': all_batches.count(),
        'report_date': timezone.now(),
    }
    return render(request, "inventory/stock_report.html", context)


def stock_report_pdf(request):
    """PDF Stock report"""
    products = Product.objects.all().order_by('name')
    today = timezone.now()
    
    total_purchase_value = Decimal('0')
    total_sale_value = Decimal('0')
    
    for product in products:
        stock_boxes = product.total_boxes or 0
        if stock_boxes > 0:
            # Calculate stock value for each product
            product.stock_value = Decimal(stock_boxes) * Decimal(product.purchase_price or 0)
            total_purchase_value += product.stock_value
            total_sale_value += Decimal(stock_boxes) * Decimal(product.sale_price or 0)
        else:
            product.stock_value = Decimal('0')
    
    context = {
        'products': products,
        'total_products': products.count(),
        'total_purchase_value': total_purchase_value,
        'total_sale_value': total_sale_value,
        'potential_profit': total_sale_value - total_purchase_value,
        'report_date': today,
    }
    
    template = get_template('inventory/stock_report_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="stock_report_{today.strftime("%Y%m%d")}.pdf"'
    
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    return response


def low_stock_report(request):
    """Report for low stock items"""
    threshold = int(request.GET.get('threshold', 5))
    products = Product.objects.filter(total_boxes__lt=threshold).order_by('total_boxes')
    
    context = {
        'products': products,
        'threshold': threshold,
        'count': products.count(),
    }
    return render(request, "inventory/low_stock_report.html", context)


def low_stock_report_pdf(request):
    """PDF Low stock report"""
    threshold = int(request.GET.get('threshold', 5))
    products = Product.objects.filter(total_boxes__lt=threshold).order_by('total_boxes')
    today = timezone.now()
    
    context = {
        'products': products,
        'threshold': threshold,
        'count': products.count(),
        'generated_at': today,
    }
    
    template = get_template('inventory/low_stock_report_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="low_stock_report_{today.strftime("%Y%m%d")}.pdf"'
    
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    return response


def expiry_report(request):
    """Report for expiring/expired medicines - now includes batch-level tracking"""
    today = timezone.now().date()
    
    # === BATCH-BASED EXPIRY TRACKING ===
    # Expired batches
    expired_batches = ProductBatch.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lt=today,
        is_active=True
    ).select_related('product').order_by('expiry_date')
    
    # Expiring within 30 days
    thirty_days = today + timedelta(days=30)
    expiring_30_batches = ProductBatch.objects.filter(
        expiry_date__isnull=False,
        expiry_date__gte=today,
        expiry_date__lte=thirty_days,
        is_active=True
    ).select_related('product').order_by('expiry_date')
    
    # Expiring 30-90 days
    ninety_days = today + timedelta(days=90)
    expiring_90_batches = ProductBatch.objects.filter(
        expiry_date__isnull=False,
        expiry_date__gt=thirty_days,
        expiry_date__lte=ninety_days,
        is_active=True
    ).select_related('product').order_by('expiry_date')
    
    # Expiring 90-180 days
    six_months = today + timedelta(days=180)
    expiring_180_batches = ProductBatch.objects.filter(
        expiry_date__isnull=False,
        expiry_date__gt=ninety_days,
        expiry_date__lte=six_months,
        is_active=True
    ).select_related('product').order_by('expiry_date')
    
    # Calculate values at risk
    expired_value = sum(b.current_packs * b.net_purchase_price_per_pack for b in expired_batches)
    expiring_30_value = sum(b.current_packs * b.net_purchase_price_per_pack for b in expiring_30_batches)
    expiring_90_value = sum(b.current_packs * b.net_purchase_price_per_pack for b in expiring_90_batches)
    
    # === LEGACY PRODUCT-BASED (for backward compatibility) ===
    expired = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lt=today
    ).order_by('expiry_date')
    
    expiring_30 = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__gte=today,
        expiry_date__lte=thirty_days
    ).order_by('expiry_date')
    
    expiring_90 = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__gt=thirty_days,
        expiry_date__lte=ninety_days
    ).order_by('expiry_date')
    
    expiring_180 = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__gt=ninety_days,
        expiry_date__lte=six_months
    ).order_by('expiry_date')
    
    context = {
        # Batch-based data (recommended)
        'expired_batches': expired_batches,
        'expiring_30_batches': expiring_30_batches,
        'expiring_90_batches': expiring_90_batches,
        'expiring_180_batches': expiring_180_batches,
        'expired_value': expired_value,
        'expiring_30_value': expiring_30_value,
        'expiring_90_value': expiring_90_value,
        'total_at_risk': expired_value + expiring_30_value,
        # Legacy product-based data
        'expired': expired,
        'expiring_30': expiring_30,
        'expiring_90': expiring_90,
        'expiring_180': expiring_180,
        'today': today,
    }
    return render(request, "inventory/expiry_report.html", context)


def expiry_report_pdf(request):
    """PDF Expiry report"""
    today = timezone.now().date()
    
    expired = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lt=today
    ).order_by('expiry_date')
    
    thirty_days = today + timedelta(days=30)
    expiring_30 = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__gte=today,
        expiry_date__lte=thirty_days
    ).order_by('expiry_date')
    
    ninety_days = today + timedelta(days=90)
    expiring_90 = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__gt=thirty_days,
        expiry_date__lte=ninety_days
    ).order_by('expiry_date')
    
    context = {
        'expired': expired,
        'expiring_30': expiring_30,
        'expiring_90': expiring_90,
        'today': today,
        'generated_at': timezone.now(),
    }
    
    template = get_template('inventory/expiry_report_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="expiry_report_{today.strftime("%Y%m%d")}.pdf"'
    
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    return response


def distributor_report(request):
    """Report by distributor/supplier"""
    from inventory.models import Distributor
    
    selected_distributor = request.GET.get('distributor', '')
    distributors = Distributor.objects.all().order_by('name')
    
    # Build distributor data
    distributor_data = []
    total_products = 0
    total_value = Decimal('0')
    total_purchases = Decimal('0')
    
    # Get products grouped by distributor
    if selected_distributor:
        dist_filter = Distributor.objects.filter(id=selected_distributor)
    else:
        dist_filter = list(distributors) + [None]  # Include products with no distributor
    
    for dist in (dist_filter if selected_distributor else distributors):
        products = Product.objects.filter(distributor=dist).order_by('name')
        if products.exists():
            dist_total_value = Decimal('0')
            for product in products:
                stock_boxes = product.total_boxes or 0
                product.stock_value = Decimal(stock_boxes) * Decimal(product.purchase_price or 0)
                dist_total_value += product.stock_value
            
            distributor_data.append({
                'distributor': dist,
                'products': products,
                'total_value': dist_total_value,
            })
            total_products += products.count()
            total_value += dist_total_value
    
    # Also add products with no distributor
    if not selected_distributor:
        no_dist_products = Product.objects.filter(distributor__isnull=True).order_by('name')
        if no_dist_products.exists():
            dist_total_value = Decimal('0')
            for product in no_dist_products:
                stock_boxes = product.total_boxes or 0
                product.stock_value = Decimal(stock_boxes) * Decimal(product.purchase_price or 0)
                dist_total_value += product.stock_value
            
            distributor_data.append({
                'distributor': None,
                'products': no_dist_products,
                'total_value': dist_total_value,
            })
            total_products += no_dist_products.count()
            total_value += dist_total_value
    
    context = {
        'distributors': distributors,
        'selected_distributor': selected_distributor,
        'distributor_data': distributor_data,
        'total_distributors': distributors.count(),
        'total_products': total_products,
        'total_value': total_value,
        'total_purchases': total_purchases,
        'report_date': timezone.now(),
    }
    return render(request, "inventory/distributor_report.html", context)


def distributor_report_pdf(request):
    """PDF Distributor report"""
    from inventory.models import Distributor
    
    today = timezone.now()
    selected_distributor = request.GET.get('distributor', '')
    distributors = Distributor.objects.all().order_by('name')
    
    # Build distributor data
    distributor_data = []
    total_products = 0
    total_value = Decimal('0')
    total_purchases = Decimal('0')
    
    for dist in distributors:
        products = Product.objects.filter(distributor=dist).order_by('name')
        if products.exists():
            dist_total_value = Decimal('0')
            for product in products:
                stock_boxes = product.total_boxes or 0
                product.stock_value = Decimal(stock_boxes) * Decimal(product.purchase_price or 0)
                dist_total_value += product.stock_value
            
            distributor_data.append({
                'distributor': dist,
                'products': products,
                'total_value': dist_total_value,
            })
            total_products += products.count()
            total_value += dist_total_value
    
    # Also add products with no distributor
    no_dist_products = Product.objects.filter(distributor__isnull=True).order_by('name')
    if no_dist_products.exists():
        dist_total_value = Decimal('0')
        for product in no_dist_products:
            stock_boxes = product.total_boxes or 0
            product.stock_value = Decimal(stock_boxes) * Decimal(product.purchase_price or 0)
            dist_total_value += product.stock_value
        
        distributor_data.append({
            'distributor': None,
            'products': no_dist_products,
            'total_value': dist_total_value,
        })
        total_products += no_dist_products.count()
        total_value += dist_total_value

    context = {
        'distributor_data': distributor_data,
        'total_distributors': distributors.count(),
        'total_products': total_products,
        'total_value': total_value,
        'total_purchases': total_purchases,
        'report_date': today,
    }
    
    template = get_template('inventory/distributor_report_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="distributor_report_{today.strftime("%Y%m%d")}.pdf"'
    
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    return response


def category_report(request):
    """Report by category"""
    from inventory.models import ProductCategory
    
    selected_category = request.GET.get('category', '')
    categories = ProductCategory.objects.all().order_by('name')
    
    # Build category data
    category_data = []
    total_products = 0
    total_value = Decimal('0')
    total_revenue = Decimal('0')
    
    for cat in categories:
        products = Product.objects.filter(category=cat).order_by('name')
        if products.exists():
            cat_total_value = Decimal('0')
            cat_total_revenue = Decimal('0')
            for product in products:
                stock_boxes = product.total_boxes or 0
                product.stock_value = Decimal(stock_boxes) * Decimal(product.purchase_price or 0)
                cat_total_value += product.stock_value
                cat_total_revenue += Decimal(stock_boxes) * Decimal(product.sale_price or 0)
                # Calculate margin
                if product.purchase_price and product.purchase_price > 0:
                    product.margin = ((product.sale_price or 0) - product.purchase_price) / product.purchase_price * 100
                else:
                    product.margin = 0
            
            category_data.append({
                'category': cat,
                'products': products,
                'total_value': cat_total_value,
            })
            total_products += products.count()
            total_value += cat_total_value
            total_revenue += cat_total_revenue
    
    # Also add products with no category
    no_cat_products = Product.objects.filter(category__isnull=True).order_by('name')
    if no_cat_products.exists():
        cat_total_value = Decimal('0')
        cat_total_revenue = Decimal('0')
        for product in no_cat_products:
            stock_boxes = product.total_boxes or 0
            product.stock_value = Decimal(stock_boxes) * Decimal(product.purchase_price or 0)
            cat_total_value += product.stock_value
            cat_total_revenue += Decimal(stock_boxes) * Decimal(product.sale_price or 0)
            if product.purchase_price and product.purchase_price > 0:
                product.margin = ((product.sale_price or 0) - product.purchase_price) / product.purchase_price * 100
            else:
                product.margin = 0
        
        category_data.append({
            'category': None,
            'products': no_cat_products,
            'total_value': cat_total_value,
        })
        total_products += no_cat_products.count()
        total_value += cat_total_value
        total_revenue += cat_total_revenue
    
    context = {
        'categories': categories,
        'selected_category': selected_category,
        'category_data': category_data,
        'total_categories': categories.count(),
        'total_products': total_products,
        'total_value': total_value,
        'total_revenue': total_revenue,
        'report_date': timezone.now(),
    }
    return render(request, "inventory/category_report.html", context)


def category_report_pdf(request):
    """PDF Category report"""
    from inventory.models import ProductCategory
    
    today = timezone.now()
    categories = ProductCategory.objects.all().order_by('name')
    
    # Build category data
    category_data = []
    total_products = 0
    total_value = Decimal('0')
    total_revenue = Decimal('0')
    
    for cat in categories:
        products = Product.objects.filter(category=cat).order_by('name')
        if products.exists():
            cat_total_value = Decimal('0')
            cat_total_revenue = Decimal('0')
            for product in products:
                stock_boxes = product.total_boxes or 0
                product.stock_value = Decimal(stock_boxes) * Decimal(product.purchase_price or 0)
                cat_total_value += product.stock_value
                cat_total_revenue += Decimal(stock_boxes) * Decimal(product.sale_price or 0)
                if product.purchase_price and product.purchase_price > 0:
                    product.margin = ((product.sale_price or 0) - product.purchase_price) / product.purchase_price * 100
                else:
                    product.margin = 0
            
            category_data.append({
                'category': cat,
                'products': products,
                'total_value': cat_total_value,
            })
            total_products += products.count()
            total_value += cat_total_value
            total_revenue += cat_total_revenue
    
    # Also add products with no category
    no_cat_products = Product.objects.filter(category__isnull=True).order_by('name')
    if no_cat_products.exists():
        cat_total_value = Decimal('0')
        cat_total_revenue = Decimal('0')
        for product in no_cat_products:
            stock_boxes = product.total_boxes or 0
            product.stock_value = Decimal(stock_boxes) * Decimal(product.purchase_price or 0)
            cat_total_value += product.stock_value
            cat_total_revenue += Decimal(stock_boxes) * Decimal(product.sale_price or 0)
            if product.purchase_price and product.purchase_price > 0:
                product.margin = ((product.sale_price or 0) - product.purchase_price) / product.purchase_price * 100
            else:
                product.margin = 0
        
        category_data.append({
            'category': None,
            'products': no_cat_products,
            'total_value': cat_total_value,
        })
        total_products += no_cat_products.count()
        total_value += cat_total_value
        total_revenue += cat_total_revenue
    
    context = {
        'category_data': category_data,
        'total_categories': categories.count(),
        'total_products': total_products,
        'total_value': total_value,
        'total_revenue': total_revenue,
        'report_date': today,
    }
    
    template = get_template('inventory/category_report_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="category_report_{today.strftime("%Y%m%d")}.pdf"'
    
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    return response


def sales_analysis_report(request):
    """Fast/Slow moving items analysis"""
    from datetime import datetime
    
    today = timezone.now()
    
    # Get date range from request
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        start_date = timezone.make_aware(start_date) if timezone.is_naive(start_date) else start_date
    else:
        start_date = today - timedelta(days=30)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        end_date = timezone.make_aware(end_date) if timezone.is_naive(end_date) else end_date
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        end_date = today
    
    # Total sales metrics - use quantity_subitems_out for tablets/units sold
    sales_data = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(
        total_sales=Sum(F('quantity_subitems_out') * F('unit_sale_price')),
        total_items=Sum('quantity_subitems_out'),
        total_transactions=Count('id')
    )
    
    # Get returns data to subtract from sales
    returns_data = InventoryTransaction.objects.filter(
        transaction_type='RET',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(
        total_returns=Sum(F('quantity_subitems') * F('unit_sale_price')),
        total_items_returned=Sum('quantity_subitems'),
        total_return_transactions=Count('id')
    )
    
    # Get expenses for the period
    expenses_data = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).aggregate(
        total_expenses=Sum('amount'),
        expense_count=Count('id')
    )
    total_expenses = expenses_data.get('total_expenses') or Decimal('0')
    expense_count = expenses_data.get('expense_count') or 0
    
    # Get expense breakdown by category
    expense_breakdown = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    total_sales = (sales_data.get('total_sales') or Decimal('0')) - (returns_data.get('total_returns') or Decimal('0'))
    total_items_sold = (sales_data.get('total_items') or 0) - (returns_data.get('total_items_returned') or 0)
    total_transactions = sales_data.get('total_transactions') or 0
    total_return_transactions = returns_data.get('total_return_transactions') or 0
    
    # Net Cash In Hand = Sales - Returns - Expenses
    net_cash_in_hand = total_sales - total_expenses
    
    # Calculate days in period
    days_in_period = (end_date - start_date).days or 1
    avg_daily_sales = total_sales / days_in_period
    
    # Fast moving (most sold) - by subitems (tablets)
    fast_moving_qs = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).values('product__id', 'product__name').annotate(
        qty_sold=Sum('quantity_subitems_out'),
        revenue=Sum(F('quantity_subitems_out') * F('unit_sale_price'))
    ).order_by('-qty_sold')[:10]
    
    fast_moving = [{'name': item['product__name'], 'qty_sold': item['qty_sold'], 'revenue': item['revenue']} for item in fast_moving_qs]
    
    # Slow moving (least sold with some sales)
    slow_moving_qs = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).values('product__id', 'product__name').annotate(
        qty_sold=Sum('quantity_subitems_out')
    ).order_by('qty_sold')[:10]
    
    slow_moving = []
    for item in slow_moving_qs:
        product = Product.objects.filter(id=item['product__id']).first()
        slow_moving.append({
            'name': item['product__name'],
            'qty_sold': item['qty_sold'],
            'current_stock': product.total_boxes if product else 0
        })
    
    # Complete sales breakdown - use subitems for tablet-level tracking
    sales_breakdown_qs = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).values('product__id', 'product__name', 'product__category__name').annotate(
        qty_sold=Sum('quantity_subitems_out'),
        revenue=Sum(F('quantity_subitems_out') * F('unit_sale_price')),
        cost=Sum(F('quantity_subitems_out') * F('unit_purchase_price'))
    ).order_by('-revenue')
    
    sales_breakdown = []
    for item in sales_breakdown_qs:
        revenue = item['revenue'] or Decimal('0')
        cost = item['cost'] or Decimal('0')
        profit = revenue - cost
        margin = (profit / revenue * 100) if revenue > 0 else 0
        sales_breakdown.append({
            'name': item['product__name'],
            'category': item['product__category__name'],
            'qty_sold': item['qty_sold'],
            'revenue': revenue,
            'cost': cost,
            'profit': profit,
            'margin': margin
        })
    
    # Batch-level sales breakdown
    batch_sales_breakdown = []
    batch_sales_qs = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date,
        batch__isnull=False  # Only batch-tracked sales
    ).values(
        'product__name', 
        'batch__batch_no', 
        'batch__expiry_date'
    ).annotate(
        qty_sold=Sum('quantity_subitems_out'),
        revenue=Sum(F('quantity_subitems_out') * F('unit_sale_price')),
        cost=Sum(F('quantity_subitems_out') * F('unit_purchase_price'))
    ).order_by('-revenue')[:20]  # Top 20 batches
    
    for item in batch_sales_qs:
        revenue = item['revenue'] or Decimal('0')
        cost = item['cost'] or Decimal('0')
        profit = revenue - cost
        margin = (profit / revenue * 100) if revenue > 0 else 0
        batch_sales_breakdown.append({
            'product_name': item['product__name'],
            'batch_no': item['batch__batch_no'],
            'expiry_date': item['batch__expiry_date'],
            'qty_sold': item['qty_sold'],
            'revenue': revenue,
            'cost': cost,
            'profit': profit,
            'margin': margin
        })
    
    # Check if viewing today's data
    today_date = today.date()
    is_today = (start_date.date() == today_date and end_date.date() == today_date)
    
    # Quick date ranges for buttons
    week_start = today - timedelta(days=today.weekday())  # Monday of this week
    month_start = today.replace(day=1)  # First day of month
    
    # Get gross sales (before returns) for the daily cash balance display
    total_sales_raw = sales_data.get('total_sales') or Decimal('0')
    
    # Convert expense category codes to display names
    expense_category_names = dict(Expense.EXPENSE_CATEGORIES)
    expense_breakdown_list = [
        {
            'category': expense_category_names.get(item['category'], item['category']),
            'total': item['total'],
            'count': item['count']
        }
        for item in expense_breakdown
    ]
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_sales_raw': total_sales_raw,
        'total_items_sold': total_items_sold,
        'total_transactions': total_transactions,
        'total_return_transactions': total_return_transactions,
        'total_returns': returns_data.get('total_returns') or Decimal('0'),
        'total_items_returned': returns_data.get('total_items_returned') or 0,
        'total_expenses': total_expenses,
        'expense_count': expense_count,
        'expense_breakdown': expense_breakdown_list,
        'net_cash_in_hand': net_cash_in_hand,
        'avg_daily_sales': avg_daily_sales,
        'fast_moving': fast_moving,
        'slow_moving': slow_moving,
        'sales_breakdown': sales_breakdown,
        'batch_sales_breakdown': batch_sales_breakdown,
        'report_date': today,
        'today': today,
        'is_today': is_today,
        'week_start': week_start,
        'month_start': month_start,
    }
    return render(request, "inventory/sales_analysis_report.html", context)


def sales_analysis_report_pdf(request):
    """PDF Sales analysis report"""
    from datetime import datetime
    
    today = timezone.now()
    
    # Get date range from request
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        start_date = timezone.make_aware(start_date) if timezone.is_naive(start_date) else start_date
    else:
        start_date = today - timedelta(days=30)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        end_date = timezone.make_aware(end_date) if timezone.is_naive(end_date) else end_date
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        end_date = today
    
    # Total sales metrics - use quantity_subitems_out for tablets sold
    sales_data = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(
        total_sales=Sum(F('quantity_subitems_out') * F('unit_sale_price')),
        total_items=Sum('quantity_subitems_out'),
        total_transactions=Count('id')
    )
    
    total_sales = sales_data.get('total_sales') or Decimal('0')
    total_items_sold = sales_data.get('total_items') or 0
    total_transactions = sales_data.get('total_transactions') or 0
    
    days_in_period = (end_date - start_date).days or 1
    avg_daily_sales = total_sales / days_in_period
    
    # Fast moving - by subitems
    fast_moving_qs = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).values('product__name').annotate(
        qty_sold=Sum('quantity_subitems_out'),
        revenue=Sum(F('quantity_subitems_out') * F('unit_sale_price'))
    ).order_by('-qty_sold')[:10]
    
    fast_moving = [{'name': item['product__name'], 'qty_sold': item['qty_sold'], 'revenue': item['revenue']} for item in fast_moving_qs]
    
    # Slow moving
    slow_moving_qs = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).values('product__id', 'product__name').annotate(
        qty_sold=Sum('quantity_subitems_out')
    ).order_by('qty_sold')[:10]
    
    slow_moving = []
    for item in slow_moving_qs:
        product = Product.objects.filter(id=item['product__id']).first()
        slow_moving.append({
            'name': item['product__name'],
            'qty_sold': item['qty_sold'],
            'current_stock': product.total_boxes if product else 0
        })
    
    # Sales breakdown - use subitems
    sales_breakdown_qs = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).values('product__name').annotate(
        qty_sold=Sum('quantity_subitems_out'),
        revenue=Sum(F('quantity_subitems_out') * F('unit_sale_price')),
        cost=Sum(F('quantity_subitems_out') * F('unit_purchase_price'))
    ).order_by('-revenue')
    
    sales_breakdown = []
    for item in sales_breakdown_qs:
        revenue = item['revenue'] or Decimal('0')
        cost = item['cost'] or Decimal('0')
        profit = revenue - cost
        margin = (profit / revenue * 100) if revenue > 0 else 0
        sales_breakdown.append({
            'name': item['product__name'],
            'qty_sold': item['qty_sold'],
            'revenue': revenue,
            'cost': cost,
            'profit': profit,
            'margin': margin
        })
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_items_sold': total_items_sold,
        'total_transactions': total_transactions,
        'avg_daily_sales': avg_daily_sales,
        'fast_moving': fast_moving,
        'slow_moving': slow_moving,
        'sales_breakdown': sales_breakdown,
        'report_date': today,
    }
    
    template = get_template('inventory/sales_analysis_report_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="sales_analysis_{today.strftime("%Y%m%d")}.pdf"'
    
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    return response


def profit_loss_report(request):
    """Profit/Loss analysis report with batch-level tracking"""
    from datetime import datetime
    
    today = timezone.now()
    
    # Get date range from request
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        start_date = timezone.make_aware(start_date) if timezone.is_naive(start_date) else start_date
    else:
        start_date = today - timedelta(days=30)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        end_date = timezone.make_aware(end_date) if timezone.is_naive(end_date) else end_date
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        end_date = today
    
    # Sales with batch information
    sales_transactions = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related('product', 'batch')
    
    # Calculate totals
    total_revenue = Decimal('0')
    total_cost = Decimal('0')
    batch_sales = []
    
    for txn in sales_transactions:
        qty = txn.quantity_subitems_out or txn.quantity_boxes_out or Decimal('0')
        sale_price = txn.unit_sale_price or Decimal('0')
        
        # Get cost from batch if available, otherwise from product
        if txn.batch:
            # Calculate per-tablet cost from batch
            items_per_pack = txn.product.items_per_product or 1
            subitems_per_item = txn.product.subitems_per_item or 1
            subitems_per_pack = items_per_pack * subitems_per_item
            cost_per_subitem = txn.batch.net_purchase_price_per_pack / Decimal(subitems_per_pack) if subitems_per_pack > 0 else Decimal('0')
        else:
            cost_per_subitem = txn.product.purchase_price_per_subitem or Decimal('0')
        
        revenue = qty * sale_price
        cost = qty * cost_per_subitem
        profit = revenue - cost
        
        total_revenue += revenue
        total_cost += cost
        
        batch_sales.append({
            'transaction': txn,
            'batch': txn.batch,
            'quantity': qty,
            'revenue': revenue,
            'cost': cost,
            'profit': profit,
        })
    
    medicine_sales = total_revenue
    
    # Expenses grouped by category
    expense_breakdown = []
    total_expenses = Decimal('0')
    
    expenses_by_category = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).values('category').annotate(total=Sum('amount'))
    
    for exp in expenses_by_category:
        expense_breakdown.append({
            'category': exp['category'] or 'Other',
            'total': exp['total']
        })
        total_expenses += exp['total'] or Decimal('0')
    
    total_cost_and_expenses = total_cost + total_expenses
    net_profit = total_revenue - total_cost - total_expenses
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Profit by batch (top performers)
    batch_profit_summary = {}
    for sale in batch_sales:
        if sale['batch']:
            batch_key = str(sale['batch'].pk)
            if batch_key not in batch_profit_summary:
                batch_profit_summary[batch_key] = {
                    'batch': sale['batch'],
                    'product_name': sale['transaction'].product.name,
                    'total_revenue': Decimal('0'),
                    'total_cost': Decimal('0'),
                    'total_profit': Decimal('0'),
                    'qty_sold': Decimal('0'),
                }
            batch_profit_summary[batch_key]['total_revenue'] += sale['revenue']
            batch_profit_summary[batch_key]['total_cost'] += sale['cost']
            batch_profit_summary[batch_key]['total_profit'] += sale['profit']
            batch_profit_summary[batch_key]['qty_sold'] += sale['quantity']
    
    # Sort by profit (top 10)
    top_batches = sorted(batch_profit_summary.values(), key=lambda x: x['total_profit'], reverse=True)[:10]
    
    # Daily breakdown (last 7 days)
    daily_breakdown = []
    for i in range(7):
        day_date = (today - timedelta(days=i)).date()
        day_start = timezone.make_aware(datetime.combine(day_date, datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(day_date, datetime.max.time()))
        
        day_sales = InventoryTransaction.objects.filter(
            transaction_type='SALE',
            created_at__gte=day_start,
            created_at__lte=day_end
        ).aggregate(
            revenue=Sum(F('quantity_subitems_out') * F('unit_sale_price')),
            cost=Sum(F('quantity_subitems_out') * F('unit_purchase_price'))
        )
        
        day_revenue = day_sales.get('revenue') or Decimal('0')
        day_cost = day_sales.get('cost') or Decimal('0')
        day_profit = day_revenue - day_cost
        day_margin = (day_profit / day_revenue * 100) if day_revenue > 0 else 0
        
        daily_breakdown.append({
            'date': day_date,
            'revenue': day_revenue,
            'cost': day_cost,
            'profit': day_profit,
            'margin': day_margin
        })
    
    daily_breakdown.reverse()  # Show oldest first
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'medicine_sales': medicine_sales,
        'total_expenses': total_expenses,
        'expense_breakdown': expense_breakdown,
        'total_cost_and_expenses': total_cost_and_expenses,
        'net_profit': net_profit,
        'profit_margin': profit_margin,
        'daily_breakdown': daily_breakdown,
        'top_batches': top_batches,
        'batch_sales_count': len([s for s in batch_sales if s['batch']]),
        'report_date': today,
    }
    return render(request, "inventory/profit_loss_report.html", context)


def profit_loss_report_pdf(request):
    """PDF Profit/Loss report"""
    from datetime import datetime
    
    today = timezone.now()
    
    # Get date range from request
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        start_date = timezone.make_aware(start_date) if timezone.is_naive(start_date) else start_date
    else:
        start_date = today - timedelta(days=30)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        end_date = timezone.make_aware(end_date) if timezone.is_naive(end_date) else end_date
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        end_date = today
    
    # Sales - use quantity_subitems_out
    sales = InventoryTransaction.objects.filter(
        transaction_type='SALE',
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(
        total_revenue=Sum(F('quantity_subitems_out') * F('unit_sale_price')),
        total_cost=Sum(F('quantity_subitems_out') * F('unit_purchase_price'))
    )
    
    total_revenue = sales.get('total_revenue') or Decimal('0')
    total_cost = sales.get('total_cost') or Decimal('0')
    medicine_sales = total_revenue
    
    # Expenses
    expense_breakdown = []
    total_expenses = Decimal('0')
    
    expenses_by_category = Expense.objects.filter(
        expense_date__gte=start_date.date(),
        expense_date__lte=end_date.date()
    ).values('category').annotate(total=Sum('amount'))
    
    for exp in expenses_by_category:
        expense_breakdown.append({
            'category': exp['category'] or 'Other',
            'total': exp['total']
        })
        total_expenses += exp['total'] or Decimal('0')
    
    total_cost_and_expenses = total_cost + total_expenses
    net_profit = total_revenue - total_cost - total_expenses
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Daily breakdown
    daily_breakdown = []
    for i in range(7):
        day_date = (today - timedelta(days=i)).date()
        day_start = timezone.make_aware(datetime.combine(day_date, datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(day_date, datetime.max.time()))
        
        day_sales = InventoryTransaction.objects.filter(
            transaction_type='SALE',
            created_at__gte=day_start,
            created_at__lte=day_end
        ).aggregate(
            revenue=Sum(F('quantity_subitems_out') * F('unit_sale_price')),
            cost=Sum(F('quantity_subitems_out') * F('unit_purchase_price'))
        )
        
        day_revenue = day_sales.get('revenue') or Decimal('0')
        day_cost = day_sales.get('cost') or Decimal('0')
        day_profit = day_revenue - day_cost
        day_margin = (day_profit / day_revenue * 100) if day_revenue > 0 else 0
        
        daily_breakdown.append({
            'date': day_date,
            'revenue': day_revenue,
            'cost': day_cost,
            'profit': day_profit,
            'margin': day_margin
        })
    
    daily_breakdown.reverse()
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'medicine_sales': medicine_sales,
        'total_expenses': total_expenses,
        'expense_breakdown': expense_breakdown,
        'total_cost_and_expenses': total_cost_and_expenses,
        'net_profit': net_profit,
        'profit_margin': profit_margin,
        'daily_breakdown': daily_breakdown,
        'report_date': today,
    }
    
    template = get_template('inventory/profit_loss_report_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="profit_loss_{today.strftime("%Y%m%d")}.pdf"'
    
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    
    return response
