from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, ListView
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from .models import Cart, CartItem, Order, OrderItem
from products.models import Product

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'orders/cart.html', {'cart': cart})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if not product.is_available or product.stock_quantity < 1:
        messages.error(request, 'Sorry, this product is currently out of stock.')
        return redirect('product_detail', slug=product.slug)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        if cart_item.quantity < product.stock_quantity:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f'Updated quantity of {product.name} in cart.')
        else:
            messages.warning(request, f'Cannot add more. Only {product.stock_quantity} available.')
    else:
        messages.success(request, f'Added {product.name} to cart.')
    
    return redirect(request.META.get('HTTP_REFERER', 'cart'))

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'increase':
            if cart_item.quantity < cart_item.product.stock_quantity:
                cart_item.quantity += 1
                cart_item.save()
            else:
                messages.warning(request, 'Maximum stock reached.')
        
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
                messages.success(request, 'Item removed from cart.')
        
        elif action == 'remove':
            cart_item.delete()
            messages.success(request, 'Item removed from cart.')
    
    return redirect('cart')

@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    
    if cart.items.count() == 0:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')
    
    addresses = request.user.addresses.all()
    
    if not addresses.exists():
        messages.info(request, 'Please add a delivery address first.')
        return redirect('add_address')
    
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'addresses': addresses,
        'default_address': addresses.filter(is_default=True).first() or addresses.first()
    })

@login_required
@transaction.atomic
def place_order(request):
    if request.method != 'POST':
        return redirect('cart')
    
    cart = get_object_or_404(Cart, user=request.user)
    address_id = request.POST.get('address_id')
    payment_method = request.POST.get('payment_method', 'mpesa')
    notes = request.POST.get('notes', '')
    
    if not address_id:
        messages.error(request, 'Please select a delivery address.')
        return redirect('checkout')
    
    address = get_object_or_404(request.user.addresses, id=address_id)
    
    # Validate stock availability
    for item in cart.items.all():
        if item.quantity > item.product.stock_quantity:
            messages.error(request, f'Insufficient stock for {item.product.name}. Available: {item.product.stock_quantity}')
            return redirect('cart')
    
    # Create order
    order = Order.objects.create(
        user=request.user,
        address=address,
        subtotal=cart.subtotal,
        delivery_fee=cart.delivery_fee,
        total=cart.total,
        payment_method=payment_method,
        notes=notes
    )
    
    # Create order items and update stock
    for item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            product_price=item.product.current_price,
            quantity=item.quantity
        )
        
        # Reduce stock
        item.product.stock_quantity -= item.quantity
        item.product.save()
    
    # Clear cart
    cart.items.all().delete()
    
    messages.success(request, f'Order placed successfully! Order #{order.order_number}')
    
    # Redirect to payment if not cash on delivery
    if payment_method == 'mpesa':
        return redirect('payment_process', order_number=order.order_number)
    
    return redirect('payment_confirmation', order_number=order.order_number)

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    slug_url_kwarg = 'order_number'
    slug_field = 'order_number'
    context_object_name = 'order'

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_vendor:
            return Order.objects.filter(
                items__product__vendor=user
            ).distinct().order_by('-created_at')
        
        return Order.objects.filter(user=user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_vendor_view'] = self.request.user.is_vendor
        return context
    
@login_required
def update_order_status(request, order_number):
    if request.method == 'POST':
        order = get_object_or_404(Order, order_number=order_number)
    
        if not request.user.is_vendor:
            messages.error(request, "Unauthorized.")
            return redirect('vendor_dashboard')
        
        new_status = request.POST.get('status')
        valid_statuses = [s[0] for s in Order.STATUS_CHOICES]
        
        if new_status in valid_statuses:
            order.status = new_status
            
            if new_status == 'delivered':
                from django.utils import timezone
                order.delivered_at = timezone.now()
                
                # Auto-mark COD as paid on delivery
                if order.payment_method == 'cash_on_delivery':
                    order.payment_status = 'paid'
                    order.paid_at = timezone.now()
            
            order.save()
            messages.success(request, f"Order #{order.order_number} updated to {order.get_status_display()}.")
        else:
            messages.error(request, "Invalid status.")
        
        return redirect(request.POST.get('next', 'vendor_dashboard'))
    return redirect('vendor_dashboard')

@login_required
def update_payment_status(request, order_number):
    if request.method == 'POST':
        order = get_object_or_404(Order, order_number=order_number)
        
        if not request.user.is_vendor:
            messages.error(request, "Unauthorized.")
            return redirect('vendor_dashboard')
        
        new_payment_status = request.POST.get('payment_status')
        valid_statuses = [s[0] for s in Order.PAYMENT_STATUS]
        
        if new_payment_status in valid_statuses:
            order.payment_status = new_payment_status
            
            if new_payment_status == 'paid':
                order.paid_at = timezone.now()
            order.save()
            messages.success(request, f"Payment status updated to {order.get_payment_status_display()}.")
        else:
            messages.error(request, "Invalid payment status.")
        
        return redirect(request.POST.get('next', 'vendor_dashboard'))
    return redirect('vendor_dashboard')