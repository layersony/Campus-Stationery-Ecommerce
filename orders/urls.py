from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/place/', views.place_order, name='place_order'),
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('order/<str:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<str:order_number>/update/', views.update_order_status, name='update_order_status'),
    path('orders/<str:order_number>/update-payment/', views.update_payment_status, name='update_payment_status'),

]