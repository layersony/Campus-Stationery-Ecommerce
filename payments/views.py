import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.models import Order

from .intasend import IntaSendAPI
from .models import Payment

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Initiate payment  –  POST /payments/process/<order_number>/
# ---------------------------------------------------------------------------

@login_required
def payment_process(request, order_number):
    if request.user.is_vendor:
        order = get_object_or_404(Order, order_number=order_number)
        email = order.user.email
        default_phone = order.user.phone_number
    elif request.user.is_student:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        email = request.user.email
        default_phone = request.user.phone_number
    else:
        messages.info(request, "Contact Admin, An Error Occured")
        return redirect('order_detail', order_number=order_number)

    if order.payment_status == "paid":
        messages.info(request, "This order has already been paid.")
        return redirect("order_detail", order_number=order_number)

    if request.method == "POST":
        phone_number = request.POST.get("phone_number", "").strip()

        if not phone_number:
            messages.error(request, "Please provide a valid M-Pesa phone number.")
            return render(request, "payments/payment_form.html", {"order": order})

        # Avoid duplicate Payment rows if user retries after a failure
        payment, _ = Payment.objects.get_or_create(
            order=order,
            defaults={
                "amount": 1, # "amount": order.total,
                "phone_number": phone_number,
                "api_ref": order.order_number,
            },
        )

        # Allow re-try on pending / failed payments
        if payment.status in ("pending", "failed"):
            payment.phone_number = phone_number
            payment.status = "pending"
            payment.failed_reason = ""
            payment.invoice_id = ""
            payment.save(update_fields=["phone_number", "status", "failed_reason", "invoice_id"])

        try:
            api = IntaSendAPI()
            response = api.stk_push(
                phone_number=phone_number,
                amount=1, # amount=int(order.total),
                order_number=order.order_number,
                email=email,
            )
        except Exception as exc:
            logger.exception("IntaSend STK push error: %s", exc)
            messages.error(request, "Could not reach payment gateway. Please try again.")
            return render(request, "payments/payment_form.html", {"order": order})

        # The SDK returns a dict; invoice data lives under the "invoice" key
        invoice = response.get("invoice", {})
        invoice_id = invoice.get("invoice_id") or invoice.get("id")

        if invoice_id:
            payment.invoice_id = invoice_id
            payment.status = "processing"
            payment.save(update_fields=["invoice_id", "status"])

            messages.success(
                request,
                "M-Pesa prompt sent to your phone. Enter your PIN to complete payment.",
            )
            return redirect("payment_waiting", payment_id=payment.id, order_number=order_number)
        else:
            # SDK returned something unexpected — log the full response
            err = response.get("detail") or response.get("message") or str(response)
            logger.error("IntaSend STK push unexpected response: %s", response)
            payment.mark_failed(reason=err)
            messages.error(request, f"Payment initiation failed: {err}")

    return render(request, "payments/payment_form.html", {
        "order": order,
        "default_phone": default_phone,
    })


# ---------------------------------------------------------------------------
# 2. Waiting / spinner page  –  GET /payments/waiting/<payment_id>/
# ---------------------------------------------------------------------------

@login_required
def payment_waiting(request, payment_id, order_number):
    if request.user.is_vendor:
        order = get_object_or_404(Order, order_number=order_number)
        payment = get_object_or_404(Payment, id=payment_id, order__user=order.user)
    elif request.user.is_student:
        payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
    else:
        messages.info(request, "Contact Admin, An Error Occured")
        return redirect('order_detail', order_number=order_number)
    
    return render(request, "payments/payment_waiting.html", {"payment": payment})


# ---------------------------------------------------------------------------
# 3. AJAX status check  –  GET /payments/check/<payment_id>/
#    Called every ~3 s by the waiting page.
# ---------------------------------------------------------------------------

@login_required
def check_payment_status(request, payment_id, order_number):
    if request.user.is_vendor:
        order = get_object_or_404(Order, order_number=order_number)
        payment = get_object_or_404(Payment, id=payment_id, order__user=order.user)
    elif request.user.is_student:
        payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
    else:
        messages.info(request, "Contact Admin, An Error Occured")
        return redirect('order_detail', order_number=order_number)
    
    # Already resolved — return immediately
    if payment.status == "completed":
        return JsonResponse({
            "status": "completed",
            "redirect_url": payment.order.get_absolute_url(),
        })

    if payment.status == "failed":
        return JsonResponse({"status": "failed", "message": payment.failed_reason})

    # Poll IntaSend using the SDK (calls POST /api/v1/payment/status/ correctly)
    if payment.invoice_id:
        try:
            api = IntaSendAPI()
            data = api.get_invoice_status(payment.invoice_id)

            # SDK returns {"invoice": {"state": "COMPLETE|FAILED|PENDING|PROCESSING", ...}}
            invoice = data.get("invoice", {})
            state = (invoice.get("state") or "").upper()

            if state == "COMPLETE":
                receipt = invoice.get("mpesa_reference") or invoice.get("account", "")
                payment.mark_completed(receipt=receipt)
                return JsonResponse({
                    "status": "completed",
                    "redirect_url": payment.order.get_absolute_url(),
                })

            if state == "FAILED":
                reason = invoice.get("failed_reason") or "Payment was not completed."
                payment.mark_failed(reason=reason)
                return JsonResponse({"status": "failed", "message": reason})

        except Exception as exc:
            # Log but don't crash — the webhook will still resolve the payment
            logger.warning("IntaSend status poll error for invoice %s: %s", payment.invoice_id, exc)

    return JsonResponse({"status": payment.status})


# ---------------------------------------------------------------------------
# 4. IntaSend webhook  –  POST /payments/webhook/
#    IntaSend POSTs JSON when an invoice state changes.
#    @csrf_exempt because it is a server-to-server call with no cookie.
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def intasend_webhook(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.warning("IntaSend webhook: invalid JSON body")
        return JsonResponse({"status": "error", "detail": "Invalid JSON"}, status=400)

    logger.debug("IntaSend webhook payload: %s", data)

    invoice   = data.get("invoice", {})
    invoice_id = invoice.get("invoice_id") or invoice.get("id", "")
    state      = (invoice.get("state") or "").upper()
    api_ref    = invoice.get("api_ref") or data.get("api_ref", "")

    if not invoice_id and not api_ref:
        return JsonResponse({"status": "ignored"})

    # Locate our Payment row — prefer invoice_id, fall back to api_ref
    payment = None
    if invoice_id:
        payment = Payment.objects.filter(invoice_id=invoice_id).first()
    if payment is None and api_ref:
        payment = Payment.objects.filter(api_ref=api_ref).first()

    if payment is None:
        logger.warning(
            "IntaSend webhook: no Payment found for invoice_id=%s api_ref=%s",
            invoice_id, api_ref,
        )
        return JsonResponse({"status": "not_found"}, status=404)

    if state == "COMPLETE":
        receipt = invoice.get("mpesa_reference") or invoice.get("account", "")
        payment.mark_completed(receipt=receipt)
    elif state == "FAILED":
        reason = invoice.get("failed_reason") or "Payment failed."
        payment.mark_failed(reason=reason)
    # PENDING / PROCESSING — no action needed; poller will pick it up

    return JsonResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# 5. Confirmation page  –  GET /payments/confirmation/<order_number>/
# ---------------------------------------------------------------------------

@login_required
def payment_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "payments/payment_confirmation.html", {"order": order})