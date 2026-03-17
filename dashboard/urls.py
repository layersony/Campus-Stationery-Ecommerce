from django.urls import path
from . import views

urlpatterns = [
    path('', views.vendor_dashboard, name='vendor_dashboard'),
    path('products/', views.vendor_products, name='vendor_products'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),


    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_dashboard/users/', views.admin_users, name='admin_users'),
    path('admin_dashboard/vendors/', views.admin_vendors, name='admin_vendors'),
    path('admin_dashboard/vendors/verify/<int:user_id>/', views.verify_vendor, name='verify_vendor'),
    path('admin_dashboard/vendors/reject/<int:user_id>/', views.reject_vendor, name='reject_vendor'),
    path('admin_dashboard/products/', views.admin_products, name='admin_products'),
    path('admin_dashboard/orders/', views.admin_orders, name='admin_orders'),
    path('admin_dashboard/orders/<str:order_number>/', views.admin_order_detail, name='admin_order_detail'),
]