from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from datetime import timedelta

from products.models import Product, Category
from orders.models import Order, OrderItem
from accounts.models import User
from django.utils.decorators import method_decorator
from django.views.generic import ListView

def vendor_required(view_func):
    return user_passes_test(lambda u: u.is_vendor or u.is_staff)(view_func)

@login_required
@vendor_required
def vendor_dashboard(request):
    vendor = request.user
    
    # Statistics
    total_products = vendor.products.count()
    total_orders = OrderItem.objects.filter(product__vendor=vendor).values('order').distinct().count()
    
    # Revenue calculation
    revenue_data = OrderItem.objects.filter(
        product__vendor=vendor,
        order__payment_status='paid'
    ).aggregate(
        total_revenue=Sum(F('product_price') * F('quantity'))
    )
    total_revenue = revenue_data['total_revenue'] or 0
    
    # Recent orders
    recent_orders = Order.objects.filter(
        items__product__vendor=vendor
    ).distinct().order_by('-created_at')[:10]
    
    # Low stock products
    low_stock = vendor.products.filter(stock_quantity__lte=10).order_by('stock_quantity')[:5]
    
    # Sales chart data (last 7 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    daily_sales = OrderItem.objects.filter(
        product__vendor=vendor,
        order__created_at__range=(start_date, end_date),
        order__payment_status='paid'
    ).values('order__created_at__date').annotate(
        total=Sum(F('product_price') * F('quantity')),
        count=Count('id')
    ).order_by('order__created_at__date')
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'low_stock': low_stock,
        'daily_sales': daily_sales,
    }
    return render(request, 'dashboard/vendor_dashboard.html', context)

@login_required
@vendor_required
def vendor_products(request):
    products = request.user.products.all().order_by('-created_at')
    return render(request, 'dashboard/vendor_products.html', {'products': products})

@login_required
@vendor_required
def add_product(request):
    if request.method == 'POST':
        # Handle form submission
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock_quantity = request.POST.get('stock_quantity')
        sku = request.POST.get('sku')
        image = request.FILES.get('image')

        try:
            category = Category.objects.get(id=category_id)
            product = Product.objects.create(
                vendor=request.user,
                category=category,
                name=name,
                description=description,
                price=float(price),
                stock_quantity=int(stock_quantity),
                sku=sku,
                image=image
            )
            messages.success(request, 'Product added successfully!')
            return redirect('vendor_products')
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
    
    categories = Category.objects.filter(is_active=True)
    return render(request, 'dashboard/add_product.html', {'categories': categories})

@login_required
@vendor_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, vendor=request.user)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.category_id = request.POST.get('category')
        product.description = request.POST.get('description')
        product.price = float(request.POST.get('price'))
        product.stock_quantity = int(request.POST.get('stock_quantity'))
        
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        
        product.save()
        messages.success(request, 'Product updated successfully!')
        return redirect('vendor_products')
    
    categories = Category.objects.filter(is_active=True)
    return render(request, 'dashboard/edit_product.html', {
        'product': product,
        'categories': categories
    })

@login_required
@vendor_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, vendor=request.user)
    product.delete()
    messages.success(request, 'Product deleted successfully!')
    return redirect('vendor_products')

class VendorOrderListView(ListView):
    model = Order
    template_name = 'dashboard/vendor_orders.html'
    context_object_name = 'orders'
    paginate_by = 10

    @method_decorator([login_required, vendor_required])
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_queryset(self):
        return Order.objects.filter(
            items__product__vendor=self.request.user
        ).distinct().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_vendor_view'] = True
        return context

# Admin Dashboard

def admin_required(view_func):
    """Decorator to check if user is staff/admin"""
    return user_passes_test(lambda u: u.is_staff or u.is_superuser)(view_func)

@login_required
@admin_required
def admin_dashboard(request):
    """Main admin dashboard view"""
    # Statistics
    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    
    # Revenue calculation
    total_revenue = Order.objects.filter(
        payment_status='paid'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Pending vendors (not verified)
    pending_vendors = User.objects.filter(
        user_type='vendor',
        is_verified=False
    ).order_by('-created_at')
    
    # Recent activity
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    recent_users = User.objects.all().order_by('-created_at')[:5]
    
    # Order status distribution
    order_status = Order.objects.values('status').annotate(count=Count('id'))
    
    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_vendors': pending_vendors,
        'pending_vendors_count': pending_vendors.count(),
        'recent_orders': recent_orders,
        'recent_users': recent_users,
        'order_status': order_status,
    }
    return render(request, 'dashboard/admin/admin_dashboard.html', context)

@login_required
@admin_required
def admin_users(request):
    """View all users"""
    users = User.objects.all().order_by('-created_at')
    
    # Filter by user type if provided
    user_type = request.GET.get('type')
    if user_type:
        users = users.filter(user_type=user_type)
    
    # Search functionality
    search = request.GET.get('q')
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(student_id__icontains=search) |
            Q(business_name__icontains=search)
        )
    
    context = {
        'users': users,
        'total_students': User.objects.filter(user_type='student').count(),
        'total_vendors': User.objects.filter(user_type='vendor').count(),
        'pending_vendors': User.objects.filter(user_type='vendor', is_verified=False).count(),
    }
    return render(request, 'dashboard/admin/admin_users.html', context)

@login_required
@admin_required
def admin_vendors(request):
    """View and manage vendors"""
    vendors = User.objects.filter(user_type='vendor').order_by('-created_at')
    
    # Filter by verification status
    status = request.GET.get('status')
    if status == 'pending':
        vendors = vendors.filter(is_verified=False)
    elif status == 'verified':
        vendors = vendors.filter(is_verified=True)
    
    context = {
        'vendors': vendors,
        'pending_count': User.objects.filter(user_type='vendor', is_verified=False).count(),
        'verified_count': User.objects.filter(user_type='vendor', is_verified=True).count(),
    }
    return render(request, 'dashboard/admin/admin_vendors.html', context)

@login_required
@admin_required
def verify_vendor(request, user_id):
    """Approve/verify a vendor"""
    vendor = get_object_or_404(User, id=user_id, user_type='vendor')
    vendor.is_verified = True
    vendor.is_active = True
    vendor.save()
    messages.success(request, f'Vendor {vendor.business_name} has been verified successfully!')
    return redirect('admin_vendors')

@login_required
@admin_required
def reject_vendor(request, user_id):
    """Reject a vendor application"""
    vendor = get_object_or_404(User, id=user_id, user_type='vendor')
    # Option 1: Delete the vendor account
    # vendor.delete()
    # messages.success(request, f'Vendor application rejected and removed.')
    
    # Option 2: Just mark as rejected (inactive)
    vendor.is_verified = False
    vendor.is_active = False
    vendor.save()
    messages.warning(request, f'Vendor {vendor.business_name} has been rejected.')
    return redirect('admin_vendors')

@login_required
@admin_required
def admin_products(request):
    """View all products (admin view)"""
    products = Product.objects.all().order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        products = products.filter(stock_status=status)
    
    # Filter by vendor
    vendor_id = request.GET.get('vendor')
    if vendor_id:
        products = products.filter(vendor_id=vendor_id)
    
    total_products = products.count()
    low_stock = Product.objects.filter(stock_quantity__lte=10).count()
    out_of_stock = Product.objects.filter(stock_quantity=0).count()
    in_stock = total_products - low_stock - out_of_stock  # Calculate here
    
    context = {
        'products': products,
        'total_products': total_products,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'in_stock': in_stock,
    }
    return render(request, 'dashboard/admin/admin_products.html', context)

@login_required
@admin_required
def admin_orders(request):
    """View all orders (admin view)"""
    orders = Order.objects.all().order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Filter by payment status
    payment = request.GET.get('payment')
    if payment:
        orders = orders.filter(payment_status=payment)
    
    context = {
        'orders': orders,
        'total_orders': orders.count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'completed_orders': Order.objects.filter(status='delivered').count(),
    }
    return render(request, 'dashboard/admin/admin_orders.html', context)

@login_required
@admin_required
def admin_order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(Order.STATUS_CHOICES):
                order.status = new_status
                if new_status == 'delivered':
                    from django.utils import timezone
                    order.delivered_at = timezone.now()
                    if order.payment_method == 'cod':
                        order.payment_status = 'paid'
                        order.paid_at = timezone.now()
                order.save()
                messages.success(request, f'Order status updated to {order.get_status_display()}')

        elif action == 'update_tracking':
            order.tracking_number = request.POST.get('tracking_number', '').strip()
            order.save()
            messages.success(request, 'Tracking number updated')

        elif action == 'update_payment':
            new_payment_status = request.POST.get('payment_status')
            if new_payment_status in dict(Order.PAYMENT_STATUS):
                order.payment_status = new_payment_status
                if new_payment_status == 'paid':
                    from django.utils import timezone
                    order.paid_at = timezone.now()
                order.save()
                messages.success(request, f'Payment status updated to {order.get_payment_status_display()}')

    context = {
        'order': order,
        'progress_steps': ['Ordered', 'Confirmed', 'Processing', 'Shipped', 'Delivered'],
    }
    return render(request, 'dashboard/admin/admin_order_detail.html', context)