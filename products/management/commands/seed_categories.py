from django.core.management.base import BaseCommand
from products.models import Category

class Command(BaseCommand):
    help = 'Seed initial product categories'

    def handle(self, *args, **kwargs):
        categories = [
            {'name': 'Notebooks & Pads', 'slug': 'notebooks-pads', 'icon': 'bi-book', 'description': 'Exercise books, spiral notebooks, and writing pads'},
            {'name': 'Writing Instruments', 'slug': 'writing-instruments', 'icon': 'bi-pen', 'description': 'Pens, pencils, markers, and highlighters'},
            {'name': 'Paper Products', 'slug': 'paper-products', 'icon': 'bi-file-text', 'description': 'Printing paper, cardstock, and specialty paper'},
            {'name': 'Office Supplies', 'slug': 'office-supplies', 'icon': 'bi-briefcase', 'description': 'Staplers, punches, tapes, and organizers'},
            {'name': 'Art Supplies', 'slug': 'art-supplies', 'icon': 'bi-palette', 'description': 'Paints, brushes, canvases, and drawing materials'},
            {'name': 'Calculators', 'slug': 'calculators', 'icon': 'bi-calculator', 'description': 'Scientific and basic calculators'},
            {'name': 'Folders & Files', 'slug': 'folders-files', 'icon': 'bi-folder', 'description': 'Document folders, binders, and filing accessories'},
            {'name': 'Tech Accessories', 'slug': 'tech-accessories', 'icon': 'bi-laptop', 'description': 'USB drives, cables, and computer accessories'},
        ]
        
        for cat_data in categories:
            Category.objects.get_or_create(slug=cat_data['slug'], defaults=cat_data)
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded categories'))