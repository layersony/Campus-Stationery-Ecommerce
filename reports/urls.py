from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    path('sales/', views.sales_report, name='sales'),
    path('orders/', views.orders_report, name='orders'),
    path('products/', views.products_report, name='products'),
    path('users/', views.users_report, name='users'),
    path('payments/', views.payments_report, name='payments'),
    path('export/<str:report_type>/', views.export_report, name='export'),
]