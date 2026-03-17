from django.core.management.base import BaseCommand
from products.models import Product
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Fix products with empty slugs'

    def handle(self, *args, **kwargs):
        fixed = 0
        for product in Product.objects.filter(slug=''):
            product.slug = slugify(product.name) or 'product'
            counter = 1
            original = product.slug
            while Product.objects.filter(slug=product.slug).exclude(pk=product.pk).exists():
                product.slug = f"{original}-{counter}"
                counter += 1
            product.save()
            fixed += 1
            self.stdout.write(f"Fixed: {product.name} -> {product.slug}")
        
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed} products'))