# inventory/forms.py
from django import forms
from decimal import Decimal
from .models import Product, InventoryTransaction

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "category", "products_in_box", "items_per_product", "subitems_per_item",
            "weight_or_quantity", "purchase_price", "purchase_margin_percent", "discount_percent",
            "rack_no", "expiry_date", "batch_no" 
        ]
        widgets = {
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
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
            "notes": forms.Textarea(attrs={"rows":3}),
        }

    def clean(self):
        data = super().clean()
        q_boxes = data.get("quantity_boxes") or Decimal('0')
        q_items = data.get("quantity_items") or Decimal('0')
        q_sub = data.get("quantity_subitems") or Decimal('0')

        if q_boxes == 0 and q_items == 0 and q_sub == 0:
            raise forms.ValidationError("Please provide at least one of boxes, packs (items) or sub-items.")
        return data
