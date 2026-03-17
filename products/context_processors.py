from orders.models import Cart
from .models import Category

def cart_context(request):
    """Make cart data available in all templates"""
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            return {
                'cart_items_count': cart.total_items,
                'cart_total': cart.total
            }
        except Cart.DoesNotExist:
            pass
    return {'cart_items_count': 0, 'cart_total': 0}

def categories_context(request):
    """Make categories available in all templates"""
    return {
        'nav_categories': Category.objects.filter(is_active=True)[:6]
    }