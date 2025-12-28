from django.core.management.base import BaseCommand
from inventory.models import Product

class Command(BaseCommand):
    help = 'Fix stock for all existing products by updating cached totals'

    def handle(self, *args, **options):
        products = Product.objects.all()
        for product in products:
            product.update_cached_stock()
            self.stdout.write(
                self.style.SUCCESS(f'Updated stock for {product.name}: {product.total_boxes} boxes, {product.total_items} items, {product.total_subitems} subitems')
            )
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {products.count()} products'))
