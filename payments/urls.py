from django.urls import path
from . import views

urlpatterns = [
    # Initiate STK push
    path("process/<str:order_number>/",      views.payment_process,       name="payment_process"),

    # Waiting / spinner page
    path("waiting/<int:payment_id>/<order_number>/",         views.payment_waiting,       name="payment_waiting"),

    # AJAX status poll (called by the waiting page every ~3 s)
    path("check/<int:payment_id>/<order_number>/",           views.check_payment_status,  name="check_payment_status"),

    # Server-to-server webhook from IntaSend
    path("webhook/",                          views.intasend_webhook,      name="intasend_webhook"),

    # Success confirmation page
    path("confirmation/<str:order_number>/",  views.payment_confirmation,  name="payment_confirmation"),
]