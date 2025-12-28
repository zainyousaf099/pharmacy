# inventory/forms.py
from django import forms
from decimal import Decimal
from .models import Product, InventoryTransaction, ProductCategory, Expense, Distributor

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "category", "medicine_form", "distributor", "products_in_box", "items_per_product", "subitems_per_item",
            "weight_or_quantity", "purchase_price", "distributor_discount_percent", "distributor_discount_pkr",
            "purchase_margin_percent", "rack_no", "expiry_date", "batch_no" 
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g., Panadol, Disprin, etc."
            }),
            "category": forms.Select(attrs={"class": "form-select"}),
            "medicine_form": forms.Select(attrs={"class": "form-select", "id": "medicine_form"}),
            "distributor": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter distributor/supplier name"
            }),
            "products_in_box": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "How many packs/boxes purchased?",
                "min": "1"
            }),
            "items_per_product": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "How many strips/sheets per pack?",
                "min": "1",
                "id": "items_per_product"
            }),
            "subitems_per_item": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "How many tablets/units per strip?",
                "min": "1",
                "id": "subitems_per_item"
            }),
            "weight_or_quantity": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g., 500mg, 100ml (optional)"
            }),
            "purchase_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Total purchase price (before discount)",
                "step": "0.01",
                "id": "id_purchase_price"
            }),
            "distributor_discount_percent": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Discount %",
                "step": "0.01",
                "id": "id_distributor_discount_percent"
            }),
            "distributor_discount_pkr": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Discount in PKR",
                "step": "0.01",
                "id": "id_distributor_discount_pkr"
            }),
            "purchase_margin_percent": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Profit margin %",
                "step": "0.01"
            }),
            "rack_no": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Rack number (optional)"
            }),
            "expiry_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "batch_no": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Batch number (optional)"
            }),
        }
        labels = {
            "name": "Medicine Name",
            "category": "Category",
            "medicine_form": "Medicine Form/Type",
            "distributor": "Distributor/Supplier",
            "products_in_box": "Number of Packs/Boxes",
            "items_per_product": "Items per Pack (Strips/Sheets)",
            "subitems_per_item": "Units per Item (Tablets/Capsules)",
            "weight_or_quantity": "Dosage/Strength",
            "purchase_price": "Gross Purchase Price",
            "distributor_discount_percent": "Distributor Discount (%)",
            "distributor_discount_pkr": "Distributor Discount (PKR)",
            "purchase_margin_percent": "Profit Margin (%)",
            "rack_no": "Rack No.",
            "expiry_date": "Expiry Date",
            "batch_no": "Batch No."
        }

class PurchaseForm(forms.ModelForm):
    """
    Form to log incoming stock (a purchase). Let the user enter how many boxes, packs (items) and subitems
    they received. We'll set transaction_type to PURCHASE on save in the view.
    """
    class Meta:
        model = InventoryTransaction
        fields = [
            "quantity_boxes", "quantity_items", "quantity_subitems", "unit_purchase_price", "notes"
        ]
        widgets = {
            "quantity_boxes": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Number of boxes/packs",
                "step": "1",
                "min": "0"
            }),
            "quantity_items": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Number of strips/sheets",
                "step": "1",
                "min": "0"
            }),
            "quantity_subitems": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Number of tablets/units",
                "step": "1",
                "min": "0"
            }),
            "unit_purchase_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Purchase price",
                "step": "0.01"
            }),
            "notes": forms.Textarea(attrs={
                "rows": 3,
                "class": "form-control",
                "placeholder": "Additional notes (optional)"
            }),
        }
        labels = {
            "quantity_boxes": "Quantity (Packs/Boxes)",
            "quantity_items": "Quantity (Strips/Sheets)",
            "quantity_subitems": "Quantity (Tablets/Units)",
            "unit_purchase_price": "Purchase Price per Pack",
            "notes": "Notes"
        }

    def clean(self):
        data = super().clean()
        q_boxes = data.get("quantity_boxes") or Decimal('0')
        q_items = data.get("quantity_items") or Decimal('0')
        q_sub = data.get("quantity_subitems") or Decimal('0')

        if q_boxes == 0 and q_items == 0 and q_sub == 0:
            raise forms.ValidationError("Please provide at least one quantity (boxes, strips, or tablets).")
        return data


class SaleForm(forms.ModelForm):
    """Form to record a sale transaction"""
    class Meta:
        model = InventoryTransaction
        fields = [
            "quantity_boxes", "quantity_items", "quantity_subitems", "unit_sale_price", "notes"
        ]
        widgets = {
            "quantity_boxes": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Packs sold",
                "step": "1",
                "min": "0"
            }),
            "quantity_items": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Strips sold",
                "step": "1",
                "min": "0"
            }),
            "quantity_subitems": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Tablets sold",
                "step": "1",
                "min": "0"
            }),
            "unit_sale_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Sale price per pack",
                "step": "0.01"
            }),
            "notes": forms.Textarea(attrs={
                "rows": 3,
                "class": "form-control",
                "placeholder": "Customer/sale notes (optional)"
            }),
        }
        labels = {
            "quantity_boxes": "Packs Sold",
            "quantity_items": "Strips Sold",
            "quantity_subitems": "Tablets Sold",
            "unit_sale_price": "Sale Price per Pack",
            "notes": "Notes"
        }

    def clean(self):
        data = super().clean()
        q_boxes = data.get("quantity_boxes") or Decimal('0')
        q_items = data.get("quantity_items") or Decimal('0')
        q_sub = data.get("quantity_subitems") or Decimal('0')

        if q_boxes == 0 and q_items == 0 and q_sub == 0:
            raise forms.ValidationError("Please provide at least one quantity to sell.")
        return data


class ExpenseForm(forms.ModelForm):
    """Form to add daily clinic expenses"""
    class Meta:
        model = Expense
        fields = ["title", "category", "amount", "expense_date", "notes"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g., Tea for staff, Electricity bill"
            }),
            "category": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Amount in PKR",
                "step": "0.01",
                "min": "0"
            }),
            "expense_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "notes": forms.Textarea(attrs={
                "rows": 3,
                "class": "form-control",
                "placeholder": "Additional details (optional)"
            }),
        }
        labels = {
            "title": "Expense Title",
            "category": "Category",
            "amount": "Amount (PKR)",
            "expense_date": "Date",
            "notes": "Notes"
        }


