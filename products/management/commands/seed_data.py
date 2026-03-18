from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Product
from accounts.models import User
import random
from django.db import transaction
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Seed vendor, categories, and products"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        User = get_user_model()

        vendor_data = {
            'username': 'campusvendor',
            'email': 'vendor@campusstationery.com',
            'first_name': 'Campus',
            'last_name': 'Vendor',
            'password': '9876Bcdefg',
            'user_type': 'vendor',
            'business_name': 'Campus Stationery Supplies',
            'business_registration': 'BS-2024-001',
            'phone_number': '+254712345678',
            'location': 'Main Campus, Student Center Building',
            'is_verified': True,
            'is_active': True,
        }

        vendor = User.objects.filter(email=vendor_data['email']).first()

        if vendor:
            self.stdout.write(self.style.WARNING(f"Vendor already exists: {vendor.email}"))
        else:
            vendor = User.objects.create_user(
                username=vendor_data['username'],
                email=vendor_data['email'],
                password=vendor_data['password'],
                first_name=vendor_data['first_name'],
                last_name=vendor_data['last_name'],
                user_type=vendor_data['user_type'],
                business_name=vendor_data['business_name'],
                business_registration=vendor_data['business_registration'],
                phone_number=vendor_data['phone_number'],
                location=vendor_data['location'],
                is_verified=vendor_data['is_verified'],
                is_active=vendor_data['is_active'],
            )
            self.stdout.write(self.style.SUCCESS(f"Vendor created: {vendor.email}"))

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

        for cat in categories:
            Category.objects.get_or_create(
                slug=cat['slug'],
                defaults=cat
            )

        self.stdout.write(self.style.SUCCESS("Categories seeded"))

        products_data = {
            'notebooks-pads': [
                {'name': 'A4 Exercise Book 200 Pages', 'price': 120, 'stock': 50, 'sku': 'NB-A4-200', 'brand': 'Campus', 'description': 'High-quality A4 exercise book with 200 ruled pages.'},
                {'name': 'Spiral Notebook A5 100 Pages', 'price': 80, 'stock': 75, 'sku': 'NB-A5-100', 'brand': 'WriteWell', 'description': 'Compact A5 spiral notebook with perforated pages.'},
                {'name': 'Hardcover Journal Premium', 'price': 350, 'stock': 30, 'sku': 'NB-JRN-001', 'brand': 'LuxWrite', 'description': 'Premium hardcover journal with 240 pages.'},
                {'name': 'Graph Paper Notebook', 'price': 150, 'stock': 40, 'sku': 'NB-GRP-001', 'brand': 'MathPro', 'description': 'A4 notebook with 5mm grid paper.'},
                {'name': 'Sticky Notes Pack 3x3', 'price': 95, 'stock': 100, 'sku': 'NB-STK-001', 'brand': 'PostIt', 'description': 'Pack of 5 colorful sticky note pads.'},
            ],
            'writing-instruments': [
                {'name': 'Ballpoint Pen Blue (Pack of 10)', 'price': 150, 'stock': 200, 'sku': 'PEN-BLU-10', 'brand': 'Bic', 'description': 'Smooth writing ballpoint pens. Pack of 10.'},
                {'name': 'Gel Pen Black 0.5mm', 'price': 45, 'stock': 150, 'sku': 'PEN-GEL-001', 'brand': 'Uni-ball', 'description': 'Premium gel pen with 0.5mm tip.'},
                {'name': 'Mechanical Pencil 0.7mm', 'price': 85, 'stock': 80, 'sku': 'PNC-MP-001', 'brand': 'Pentel', 'description': 'Automatic mechanical pencil with eraser.'},
                {'name': 'Highlighter Set 4 Colors', 'price': 120, 'stock': 60, 'sku': 'PEN-HL-004', 'brand': 'Stabilo', 'description': 'Set of 4 fluorescent highlighters.'},
                {'name': 'Permanent Marker Black', 'price': 65, 'stock': 90, 'sku': 'PEN-MK-001', 'brand': 'Sharpie', 'description': 'Permanent marker with quick-drying ink.'},
                {'name': 'Whiteboard Marker Set', 'price': 180, 'stock': 45, 'sku': 'PEN-WB-004', 'brand': 'Expo', 'description': 'Set of 4 dry-erase markers.'},
            ],
            'paper-products': [
                {'name': 'A4 Copy Paper Ream (500 sheets)', 'price': 450, 'stock': 100, 'sku': 'PAP-A4-500', 'brand': 'Double A', 'description': 'Premium quality A4 copy paper, 80gsm.'},
                {'name': 'A3 Copy Paper Ream (500 sheets)', 'price': 650, 'stock': 40, 'sku': 'PAP-A3-500', 'brand': 'Double A', 'description': 'Large format A3 paper.'},
                {'name': 'Colored Cardstock Pack', 'price': 280, 'stock': 35, 'sku': 'PAP-CST-001', 'brand': 'ArtColor', 'description': '50 sheets of A4 colored cardstock.'},
                {'name': 'Photo Paper Glossy 20 sheets', 'price': 320, 'stock': 25, 'sku': 'PAP-PHO-001', 'brand': 'HP', 'description': 'Premium glossy photo paper.'},
                {'name': 'Continuous Computer Paper', 'price': 550, 'stock': 20, 'sku': 'PAP-COMP-001', 'brand': 'PrintPro', 'description': 'Carbonless continuous form paper.'},
            ],
            'office-supplies': [
                {'name': 'Desktop Stapler with Staples', 'price': 195, 'stock': 40, 'sku': 'OFF-STP-001', 'brand': 'Kangaro', 'description': 'Durable metal stapler with 1000 staples.'},
                {'name': 'Paper Punch 2-Hole', 'price': 145, 'stock': 35, 'sku': 'OFF-PCH-001', 'brand': 'Kangaro', 'description': 'Heavy-duty 2-hole punch.'},
                {'name': 'Clear Tape Dispenser', 'price': 125, 'stock': 55, 'sku': 'OFF-TAP-001', 'brand': '3M', 'description': 'Desktop tape dispenser.'},
                {'name': 'Document Clips Box (50 pcs)', 'price': 85, 'stock': 70, 'sku': 'OFF-CLP-001', 'brand': 'OfficeMate', 'description': 'Box of 50 metal binder clips.'},
                {'name': 'Desk Organizer Set', 'price': 450, 'stock': 20, 'sku': 'OFF-ORG-001', 'brand': 'OrganizeIt', 'description': '5-piece desk organizer set.'},
                {'name': 'Rubber Bands Pack 100g', 'price': 75, 'stock': 60, 'sku': 'OFF-RUB-001', 'brand': 'Elastico', 'description': 'Assorted size rubber bands.'},
            ],
            'art-supplies': [
                {'name': 'Watercolor Paint Set 24 Colors', 'price': 650, 'stock': 25, 'sku': 'ART-WC-024', 'brand': 'Sakura', 'description': 'Professional watercolor paint set.'},
                {'name': 'Acrylic Paint Set 12 Colors', 'price': 480, 'stock': 30, 'sku': 'ART-AC-012', 'brand': 'Reeves', 'description': 'Vibrant acrylic paints.'},
                {'name': 'Drawing Pencils Set (12 grades)', 'price': 320, 'stock': 40, 'sku': 'ART-PEN-012', 'brand': 'Faber-Castell', 'description': 'Professional drawing pencils.'},
                {'name': 'Canvas Board 8x10 inch', 'price': 180, 'stock': 50, 'sku': 'ART-CAN-001', 'brand': 'ArtPro', 'description': 'Primed canvas board. Pack of 2.'},
                {'name': 'Paint Brush Set 10 pcs', 'price': 380, 'stock': 35, 'sku': 'ART-BRS-010', 'brand': 'ArtMaster', 'description': 'Assorted paint brushes.'},
                {'name': 'Sketch Pad A3 50 Sheets', 'price': 280, 'stock': 45, 'sku': 'ART-SKT-001', 'brand': 'Canson', 'description': 'High-quality drawing paper.'},
            ],
            'calculators': [
                {'name': 'Scientific Calculator FX-991', 'price': 1200, 'stock': 30, 'sku': 'CAL-SCI-001', 'brand': 'Casio', 'description': 'Advanced scientific calculator with 417 functions.'},
                {'name': 'Basic Calculator Desktop', 'price': 350, 'stock': 50, 'sku': 'CAL-BAS-001', 'brand': 'Citizen', 'description': 'Large display desktop calculator.'},
                {'name': 'Graphing Calculator', 'price': 4500, 'stock': 15, 'sku': 'CAL-GRF-001', 'brand': 'Texas Instruments', 'description': 'Professional graphing calculator.'},
                {'name': 'Financial Calculator', 'price': 2800, 'stock': 20, 'sku': 'CAL-FIN-001', 'brand': 'HP', 'description': 'Business calculator.'},
                {'name': 'Student Calculator Basic', 'price': 180, 'stock': 100, 'sku': 'CAL-STD-001', 'brand': 'Casio', 'description': 'Portable student calculator.'},
            ],
            'folders-files': [
                {'name': 'Manila Folder Pack 50', 'price': 220, 'stock': 60, 'sku': 'FIL-MAN-050', 'brand': 'OfficePro', 'description': 'Standard letter-size manila folders.'},
                {'name': 'Ring Binder A4 2-inch', 'price': 195, 'stock': 40, 'sku': 'FIL-RB-001', 'brand': 'Bantex', 'description': 'Durable PVC ring binder.'},
                {'name': 'Document Wallet A4 Zip', 'price': 85, 'stock': 80, 'sku': 'FIL-DW-001', 'brand': 'ZipFile', 'description': 'Transparent plastic wallet.'},
                {'name': 'Expanding File 13 Pockets', 'price': 280, 'stock': 35, 'sku': 'FIL-EF-013', 'brand': 'Smead', 'description': 'Accordion-style expanding file.'},
                {'name': 'Presentation Folder A4', 'price': 45, 'stock': 100, 'sku': 'FIL-PF-001', 'brand': 'GlossyPro', 'description': 'Glossy presentation folder. Pack of 10.'},
                {'name': 'Archive Box Legal Size', 'price': 150, 'stock': 40, 'sku': 'FIL-AB-001', 'brand': 'StoreIt', 'description': 'Heavy-duty archive box.'},
            ],
            'tech-accessories': [
                {'name': 'USB Flash Drive 32GB', 'price': 450, 'stock': 50, 'sku': 'TEC-USB-032', 'brand': 'SanDisk', 'description': 'Reliable USB 3.0 flash drive.'},
                {'name': 'USB Flash Drive 64GB', 'price': 650, 'stock': 40, 'sku': 'TEC-USB-064', 'brand': 'SanDisk', 'description': 'High-speed USB 3.0 flash drive.'},
                {'name': 'HDMI Cable 2m', 'price': 320, 'stock': 30, 'sku': 'TEC-HDM-002', 'brand': 'Belkin', 'description': 'High-quality HDMI cable.'},
                {'name': 'Laptop Sleeve 15.6 inch', 'price': 850, 'stock': 25, 'sku': 'TEC-SLV-001', 'brand': 'CaseLogic', 'description': 'Padded laptop sleeve.'},
                {'name': 'Wireless Mouse', 'price': 480, 'stock': 35, 'sku': 'TEC-MOU-001', 'brand': 'Logitech', 'description': 'Ergonomic wireless mouse.'},
                {'name': 'USB-C to USB Adapter', 'price': 180, 'stock': 45, 'sku': 'TEC-ADP-001', 'brand': 'Anker', 'description': 'Compact USB-C adapter.'},
                {'name': 'Webcam HD 1080p', 'price': 1800, 'stock': 20, 'sku': 'TEC-WEB-001', 'brand': 'Logitech', 'description': 'Full HD webcam with microphone.'},
            ],
        }

        created_count = 0

        for category_slug, products in products_data.items():
            try:
                category = Category.objects.get(slug=category_slug)

                for prod in products:
                    base_slug = slugify(prod['name'])
                    slug = base_slug
                    counter = 1

                    while Product.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    product, created = Product.objects.get_or_create(
                        sku=prod['sku'],
                        defaults={
                            'name': prod['name'],
                            'slug': slug,
                            'description': prod['description'],
                            'price': prod['price'],
                            'stock_quantity': prod['stock'],
                            'category': category,
                            'vendor': vendor,
                            'brand': prod.get('brand', ''),
                            'is_available': True,
                            'is_featured': random.choice([True, False]),
                        }
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(f"Created: {product.name}")
                    else:
                        self.stdout.write(f"Skipped: {product.name}")

            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Category '{category_slug}' not found"))

        self.stdout.write(self.style.SUCCESS(f"""
                                    Seed complete: {created_count} products created
                                    
                                    Vendor login details:
                                    Vendor: {vendor.email}
                                    Password: 9876Bcdefg
                                             """))