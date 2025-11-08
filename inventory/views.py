# inventory/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from decimal import Decimal
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
from django.http import JsonResponse

from .models import Product, InventoryTransaction, ProductCategory, Expense
from .forms import ProductForm, PurchaseForm, SaleForm, ExpenseForm

def dashboard(request):
    """Dashboard showing inventory summary"""
    total_products = Product.objects.count()
    total_categories = ProductCategory.objects.count()
    low_stock_products = Product.objects.filter(total_boxes__lt=5).count()
    
    recent_transactions = InventoryTransaction.objects.all().order_by('-created_at')[:10]
    
    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'low_stock_products': low_stock_products,
        'recent_transactions': recent_transactions,
    }
    return render(request, "inventory/dashboard.html", context)

def product_list(request):
    products = Product.objects.all().order_by('name')
    return render(request, "inventory/product_list.html", {"products": products})

def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            # ensure required numeric defaults
            if product.products_in_box < 1: product.products_in_box = 1
            if product.items_per_product < 1: product.items_per_product = 1
            if product.subitems_per_item < 1: product.subitems_per_item = 1
            product.save()
            messages.success(request, f"Product '{product.name}' created successfully! Purchase Price per Pack: {product.purchase_price / product.products_in_box}, per Item: {product.purchase_price_per_item}, per Tablet: {product.purchase_price_per_subitem}")
            return redirect("inventory:product_list")
    else:
        form = ProductForm()
    return render(request, "inventory/product_create.html", {"form": form})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    transactions = product.transactions.all().order_by('-created_at')[:50]
    return render(request, "inventory/product_detail.html", {"product": product, "transactions": transactions})

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
            # If user didn't set unit_purchase_price on form, take product.purchase_price as fallback
            if not txn.unit_purchase_price or txn.unit_purchase_price == Decimal('0'):
                txn.unit_purchase_price = product.purchase_price / product.products_in_box
            txn.save()
            messages.success(request, "Purchase recorded and stock updated successfully!")
            return redirect("inventory:product_detail", pk=product.pk)
    else:
        initial = {
            "unit_purchase_price": product.purchase_price / product.products_in_box
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
    """Record a sale transaction"""
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = SaleForm(request.POST)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.product = product
            txn.transaction_type = InventoryTransaction.SALE
            # If user didn't set unit_sale_price, use product's sale price
            if not txn.unit_sale_price or txn.unit_sale_price == Decimal('0'):
                txn.unit_sale_price = product.sale_price / product.products_in_box if product.sale_price else Decimal('0')
            txn.save()
            messages.success(request, "Sale recorded successfully!")
            return redirect("inventory:product_detail", pk=product.pk)
    else:
        initial = {
            "unit_sale_price": product.sale_price / product.products_in_box if product.sale_price else Decimal('0')
        }
        form = SaleForm(initial=initial)

    context = {
        "product": product,
        "form": form,
        "items_per_product": product.items_per_product,
        "subitems_per_item": product.subitems_per_item,
    }
    return render(request, "inventory/add_sale.html", context)


def reports(request):
    """Sales, Purchase, and Expense Reports"""
    # Get date filter from request
    period = request.GET.get('period', 'month')  # week, month, year
    
    today = timezone.now()
    
    if period == 'week':
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
    
    # Calculate profit/loss
    total_sales = sales.get('total_sales') or Decimal('0')
    total_purchases = purchases.get('total_purchases') or Decimal('0')
    total_expenses = expenses.get('total_expenses') or Decimal('0')
    profit_loss = total_sales - total_purchases - total_expenses
    
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
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        'total_expenses': total_expenses,
        'profit_loss': profit_loss,
        'sales_quantity': sales.get('total_quantity') or 0,
        'purchase_quantity': purchases.get('total_quantity') or 0,
        'top_products': top_products,
        'recent_sales': recent_sales,
        'recent_purchases': recent_purchases,
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


def product_update(request, pk):
    """Update product details and prices"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            updated_product = form.save(commit=False)
            # ensure required numeric defaults
            if updated_product.products_in_box < 1: updated_product.products_in_box = 1
            if updated_product.items_per_product < 1: updated_product.items_per_product = 1
            if updated_product.subitems_per_item < 1: updated_product.subitems_per_item = 1
            updated_product.save()
            messages.success(request, f"Product '{updated_product.name}' updated successfully!")
            return redirect("inventory:product_detail", pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    context = {
        "form": form,
        "product": product,
        "is_update": True,
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
