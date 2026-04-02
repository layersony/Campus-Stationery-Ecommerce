from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, Avg, F, Q, FloatField
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import json

from orders.models import Order, OrderItem
from products.models import Product, Category
from accounts.models import User
from payments.models import Payment


def is_admin_or_vendor(user):
    return user.is_authenticated and (user.is_admin or user.is_vendor)


@login_required
@user_passes_test(is_admin_or_vendor)
def reports_dashboard(request):
    """Main reports dashboard with overview metrics"""
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)
    
    # Date range from request or default to last 30 days
    start_date = request.GET.get('start_date', thirty_days_ago.isoformat())
    end_date = request.GET.get('end_date', today.isoformat())
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date = thirty_days_ago
        end_date = today
    
    # Base queryset for date range
    date_filter = Q(created_at__date__gte=start_date, created_at__date__lte=end_date)
    
    # Sales Metrics
    orders = Order.objects.filter(date_filter)
    total_revenue = orders.filter(payment_status='paid').aggregate(
        total=Sum('total')
    )['total'] or 0
    
    total_orders = orders.count()
    completed_orders = orders.filter(status='delivered').count()
    
    # Previous period comparison
    prev_start = start_date - (end_date - start_date)
    prev_end = start_date - timedelta(days=1)
    prev_filter = Q(created_at__date__gte=prev_start, created_at__date__lte=prev_end)
    
    prev_revenue = Order.objects.filter(
        prev_filter, payment_status='paid'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    prev_orders = Order.objects.filter(prev_filter).count()
    
    # Calculate growth percentages
    revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue else 0
    orders_growth = ((total_orders - prev_orders) / prev_orders * 100) if prev_orders else 0
    
    # User Metrics
    new_users = User.objects.filter(date_filter).count()
    total_customers = User.objects.filter(user_type='student').count()
    
    # Product Metrics
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=10, is_available=True
    ).count()
    out_of_stock = Product.objects.filter(stock_quantity=0).count()
    
    # Payment Metrics
    payment_stats = Payment.objects.filter(date_filter).aggregate(
        total_payments=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        failed=Count('id', filter=Q(status='failed')),
        total_amount=Sum('amount', filter=Q(status='completed'))
    )
    
    # Recent activity
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    # Top products
    top_products = OrderItem.objects.filter(
        order__created_at__date__gte=start_date,
        order__created_at__date__lte=end_date
    ).values(
        'product_name', 'product__image'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=Sum(F('product_price') * F('quantity'))
    ).order_by('-total_sold')[:5]
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'revenue_growth': revenue_growth,
        'orders_growth': orders_growth,
        'new_users': new_users,
        'total_customers': total_customers,
        'low_stock_products': low_stock_products,
        'out_of_stock': out_of_stock,
        'payment_stats': payment_stats,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'conversion_rate': (completed_orders / total_orders * 100) if total_orders else 0,
    }
    
    return render(request, 'reports/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_vendor)
def sales_report(request):
    """Detailed sales analytics"""
    period = request.GET.get('period', 'daily')  # daily, weekly, monthly
    days = int(request.GET.get('days', 30))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Determine truncation based on period
    if period == 'monthly':
        trunc_func = TruncMonth
        date_format = '%b %Y'
    elif period == 'weekly':
        trunc_func = TruncWeek
        date_format = 'Week %W'
    else:
        trunc_func = TruncDate
        date_format = '%b %d'
    
    # Sales trend data
    sales_data = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        payment_status='paid'
    ).annotate(
        period=trunc_func('created_at')
    ).values('period').annotate(
        revenue=Sum('total'),
        orders=Count('id'),
        avg_order_value=Avg('total')
    ).order_by('period')
    
    # Category performance
    category_sales = OrderItem.objects.filter(
        order__created_at__date__gte=start_date,
        order__created_at__date__lte=end_date,
        order__payment_status='paid'
    ).values(
        'product__category__name'
    ).annotate(
        revenue=Sum(F('product_price') * F('quantity')),
        items_sold=Sum('quantity')
    ).order_by('-revenue')
    
    # Payment method breakdown
    payment_methods = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        payment_status='paid'
    ).values('payment_method').annotate(
        count=Count('id'),
        revenue=Sum('total')
    )
    
    context = {
        'sales_data': list(sales_data),
        'category_sales': category_sales,
        'payment_methods': payment_methods,
        'period': period,
        'days': days,
        'total_revenue': sum(d['revenue'] for d in sales_data),
        'total_orders': sum(d['orders'] for d in sales_data),
    }
    
    return render(request, 'reports/sales.html', context)


@login_required
@user_passes_test(is_admin_or_vendor)
def orders_report(request):
    """Order status and fulfillment analytics"""
    status_filter = request.GET.get('status', 'all')
    date_from = request.GET.get('date_from', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', timezone.now().strftime('%Y-%m-%d'))
    
    orders = Order.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    # Status distribution
    status_distribution = Order.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).values('status').annotate(count=Count('id')).order_by('-count')
    
    # Daily order volume
    daily_orders = Order.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id'),
        revenue=Sum('total')
    ).order_by('date')
    
    # Fulfillment metrics
    avg_fulfillment_time = Order.objects.filter(
        status='delivered',
        delivered_at__isnull=False,
        created_at__date__gte=date_from
    ).annotate(
        fulfillment_time=F('delivered_at') - F('created_at')
    ).aggregate(avg_time=Avg('fulfillment_time'))
    
    context = {
        'orders': orders.select_related('user', 'address')[:50],
        'status_distribution': status_distribution,
        'daily_orders': list(daily_orders),
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'avg_fulfillment_time': avg_fulfillment_time['avg_time'],
    }
    
    return render(request, 'reports/orders.html', context)


@login_required
@user_passes_test(is_admin_or_vendor)
def products_report(request):
    """Product performance and inventory analytics"""
    # Top selling products
    top_selling = OrderItem.objects.filter(
        order__payment_status='paid'
    ).values(
        'product__id', 'product__name', 'product__sku', 
        'product__stock_quantity', 'product__stock_status'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=Sum(F('product_price') * F('quantity')),
        avg_price=Avg('product_price')
    ).order_by('-total_sold')[:20]
    
    # Inventory status
    inventory_summary = {
        'in_stock': Product.objects.filter(stock_status='in_stock').count(),
        'low_stock': Product.objects.filter(stock_status='low_stock').count(),
        'out_of_stock': Product.objects.filter(stock_status='out_of_stock').count(),
        'total_value': Product.objects.filter(
            stock_quantity__gt=0
        ).aggregate(
            value=Sum(F('price') * F('stock_quantity'))
        )['value'] or 0
    }
    
    # Category performance
    category_performance = Product.objects.values(
        'category__name'
    ).annotate(
        product_count=Count('id'),
        avg_price=Avg('price'),
        total_stock=Sum('stock_quantity')
    ).order_by('-product_count')
    
    # Products needing attention
    attention_needed = Product.objects.filter(
        Q(stock_quantity__lte=5) | Q(views_count__gt=100, stock_quantity__lte=10)
    ).order_by('stock_quantity')[:10]
    
    context = {
        'top_selling': top_selling,
        'inventory_summary': inventory_summary,
        'category_performance': category_performance,
        'attention_needed': attention_needed,
    }
    
    return render(request, 'reports/products.html', context)


@login_required
@user_passes_test(is_admin_or_vendor)
def users_report(request):
    """User analytics and demographics"""
    # User type distribution
    user_types = User.objects.values('user_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Registration trends
    reg_trends = User.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=90)
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Top customers by order value
    top_customers = User.objects.filter(
        user_type='student',
        orders__payment_status='paid'
    ).annotate(
        total_spent=Sum('orders__total'),
        order_count=Count('orders')
    ).order_by('-total_spent')[:10]
    
    # Vendor performance
    vendor_performance = User.objects.filter(
        user_type='vendor',
        is_verified=True
    ).annotate(
        product_count=Count('products'),
        total_sales=Sum('products__orderitem__quantity', 
                       filter=Q(products__orderitem__order__payment_status='paid'))
    ).order_by('-total_sales')[:10]
    
    context = {
        'user_types': user_types,
        'reg_trends': list(reg_trends),
        'top_customers': top_customers,
        'vendor_performance': vendor_performance,
        'total_users': User.objects.count(),
        'verified_vendors': User.objects.filter(user_type='vendor', is_verified=True).count(),
    }
    
    return render(request, 'reports/users.html', context)


@login_required
@user_passes_test(is_admin_or_vendor)
def payments_report(request):
    """Payment and transaction analytics"""
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Payment status distribution
    status_dist = Payment.objects.filter(
        created_at__gte=start_date
    ).values('status').annotate(
        count=Count('id'),
        amount=Sum('amount')
    ).order_by('-count')
    
    # Daily payment volume
    daily_payments = Payment.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Sum('amount', filter=Q(status='completed')),
        count=Count('id', filter=Q(status='completed')),
        failed=Count('id', filter=Q(status='failed'))
    ).order_by('date')
    
    # Success rate over time
    total_payments = Payment.objects.filter(created_at__gte=start_date).count()
    successful_payments = Payment.objects.filter(
        created_at__gte=start_date, 
        status='completed'
    ).count()
    success_rate = (successful_payments / total_payments * 100) if total_payments else 0
    
    # M-Pesa specific metrics
    mpesa_stats = Payment.objects.filter(
        created_at__gte=start_date,
        status='completed'
    ).aggregate(
        total_transactions=Count('id'),
        total_volume=Sum('amount'),
        avg_transaction=Avg('amount')
    )
    
    context = {
        'status_distribution': status_dist,
        'daily_payments': list(daily_payments),
        'success_rate': success_rate,
        'mpesa_stats': mpesa_stats,
        'days': days,
    }
    
    return render(request, 'reports/payments.html', context)


@login_required
@user_passes_test(is_admin_or_vendor)
def export_report(request, report_type):
    """Export reports as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{timezone.now().date()}.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'sales':
        writer.writerow(['Date', 'Revenue', 'Orders', 'Avg Order Value'])
        data = Order.objects.filter(payment_status='paid').annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            revenue=Sum('total'),
            orders=Count('id'),
            avg=Avg('total')
        ).order_by('date')
        
        for row in data:
            writer.writerow([row['date'], row['revenue'], row['orders'], row['avg']])
    
    elif report_type == 'orders':
        writer.writerow(['Order #', 'Customer', 'Date', 'Status', 'Total', 'Items'])
        orders = Order.objects.select_related('user').prefetch_related('items').all()[:1000]
        
        for order in orders:
            writer.writerow([
                order.order_number,
                order.user.get_full_name(),
                order.created_at,
                order.status,
                order.total,
                order.total_items
            ])
    
    elif report_type == 'products':
        writer.writerow(['Product', 'SKU', 'Stock', 'Status', 'Total Sold', 'Revenue'])
        products = Product.objects.annotate(
            sold=Sum('orderitem__quantity', filter=Q(orderitem__order__payment_status='paid')),
            revenue=Sum(F('orderitem__product_price') * F('orderitem__quantity'), 
                       filter=Q(orderitem__order__payment_status='paid'))
        ).order_by('-sold')
        
        for p in products:
            writer.writerow([p.name, p.sku, p.stock_quantity, p.stock_status, p.sold or 0, p.revenue or 0])
    
    return response