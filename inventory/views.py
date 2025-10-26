# inventory/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from decimal import Decimal

from .models import Product, InventoryTransaction, ProductCategory
from .forms import ProductForm, PurchaseForm

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
            messages.success(request, "Product created.")
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
                txn.unit_purchase_price = product.purchase_price
            txn.save()
            messages.success(request, "Purchase recorded and stock updated.")
            return redirect("inventory:product_detail", pk=product.pk)
    else:
        initial = {
            "unit_purchase_price": product.purchase_price
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



