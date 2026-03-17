# Features Implemented
- User Management: Separate registration for Students & Vendors
- Product Catalog: Categories, search, filters, reviews, wishlist
- Shopping Cart: Session-based cart with stock validation
- Order System: Complete order lifecycle with status tracking
- M-Pesa Integration: STK Push payment processing
- Vendor Dashboard: Product management, sales analytics
- Admin Panel: System-wide oversight and management
- Responsive Design: Mobile-first Bootstrap 5 interface
- Real-time Stock: Automatic stock status updates

# Setup Instructions
### 1. Install Requirements:
```bash
pip install -r requirements.txt
```

### 2. Setup MySQL Database:
```bash
python setup_db.py
```

### 3. Run Migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Run Migrations:
```bash
python manage.py createsuperuser
```

### 5. Seed Categories:
```bash
python manage.py seed_categories
```

### 6. Run Development Server:
```bash
python manage.py runserver
```
