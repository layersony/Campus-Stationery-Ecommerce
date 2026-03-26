from django.db import models
from orders.models import Order


class Payment(models.Model):
    STATUS_CHOICES = (
        ("pending",    "Pending"),
        ("processing", "Processing"),
        ("completed",  "Completed"),
        ("failed",     "Failed"),
        ("cancelled",  "Cancelled"),
    )

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="payment"
    )

    # --- IntaSend identifiers (replaces MerchantRequestID / CheckoutRequestID) ---
    invoice_id = models.CharField(
        max_length=100, blank=True,
        help_text="IntaSend invoice_id returned after STK push initiation",
    )
    api_ref = models.CharField(
        max_length=100, blank=True,
        help_text="The order_number we sent as api_ref; echoed back in callbacks",
    )

    # --- Core payment fields ---
    amount        = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number  = models.CharField(max_length=15)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # --- Result details (populated by webhook / poll) ---
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    failed_reason        = models.TextField(blank=True)

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.invoice_id or 'N/A'} – {self.status}"

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def mark_completed(self, receipt: str = ""):
        self.status = "completed"
        self.mpesa_receipt_number = receipt
        self.save(update_fields=["status", "mpesa_receipt_number", "updated_at"])

        # Mirror on order
        from django.utils import timezone
        self.order.payment_status = "paid"
        self.order.status = "confirmed"
        self.order.paid_at = timezone.now()
        self.order.save(update_fields=["payment_status", "status", "paid_at"])

    def mark_failed(self, reason: str = ""):
        self.status = "failed"
        self.failed_reason = reason
        self.save(update_fields=["status", "failed_reason", "updated_at"])