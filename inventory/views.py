# inventory/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from decimal import Decimal
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
from django.http import JsonResponse, HttpResponse
import csv
from django.template.loader import get_template
from xhtml2pdf import pisa

from .models import Product, InventoryTransaction, ProductCategory, Expense
from .forms import ProductForm, PurchaseForm, SaleForm, ExpenseForm

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


def expense_reports(request):
    """Expense Reports - Weekly, Monthly, and Yearly"""
    # Get date filter from request
    period = request.GET.get('period', 'month')  # week, month, year
    
    today = timezone.now()
    
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())  # Start of week (Monday)
        end_date = start_date + timedelta(days=7)
        title = "Weekly Expense Report"
    elif period == 'year':
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31, 23, 59, 59)
        title = "Yearly Expense Report"
    else:  # month (default)
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
    writer.writerow(['Date', 'Title', 'Category', 'Amount', 'Description'])
    for expense in all_expenses:
        writer.writerow([
            expense.expense_date.strftime('%Y-%m-%d'),
            expense.title,
            expense.category,
            f'Rs. {expense.amount:,.2f}',
            expense.description or ''
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
    
    context = {
        'title': title,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        'total_expenses': total_expenses,
        'profit_loss': profit_loss,
        'sales_quantity': sales.get('total_quantity') or 0,
        'purchase_quantity': purchases.get('total_quantity') or 0,
        'all_sales': all_sales,
        'all_purchases': all_purchases,
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
