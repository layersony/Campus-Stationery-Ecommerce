from django.db import models
from orders.models import Order

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=100, unique=True)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result_code = models.CharField(max_length=10, blank=True)
    result_desc = models.TextField(blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"