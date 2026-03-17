from django.urls import path
from . import views

urlpatterns = [
    path('process/<str:order_number>/', views.payment_process, name='payment_process'),
    path('waiting/<int:payment_id>/', views.payment_waiting, name='payment_waiting'),
    path('check/<int:payment_id>/', views.check_payment_status, name='check_payment_status'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    path('confirmation/<str:order_number>/', views.payment_confirmation, name='payment_confirmation'),
]