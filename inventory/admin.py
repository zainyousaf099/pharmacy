# inventory/admin.py
from django.contrib import admin
from .models import Product, InventoryTransaction, ProductCategory, Expense

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "total_boxes", "total_items", "total_subitems", "purchase_price")
    search_fields = ("name",)

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ("product", "transaction_type", "quantity_boxes", "quantity_items", "quantity_subitems", "created_at")
    list_filter = ("transaction_type",)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "amount", "expense_date", "created_at")
    list_filter = ("category", "expense_date")
    search_fields = ("title", "notes")

admin.site.register(ProductCategory)
    