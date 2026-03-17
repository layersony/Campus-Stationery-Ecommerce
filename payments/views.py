from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import json
import uuid

from .models import Payment
from .mpesa import MpesaAPI
from orders.models import Order

@login_required
def payment_process(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if order.payment_status == 'paid':
        messages.info(request, 'This order has already been paid.')
        return redirect('order_detail', order_number=order_number)
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        
        if not phone_number:
            messages.error(request, 'Please provide a phone number.')
            return render(request, 'payments/payment_form.html', {'order': order})
        
        # Create payment record
        transaction_id = str(uuid.uuid4()).replace('-', '')[:20]
        payment = Payment.objects.create(
            order=order,
            transaction_id=transaction_id,
            amount=order.total,
            phone_number=phone_number
        )
        
        # Initiate M-Pesa STK Push
        mpesa = MpesaAPI()
        callback_url = request.build_absolute_uri('/payments/callback/')
        
        response = mpesa.stk_push(
            phone_number=phone_number,
            amount=int(order.total),
            account_reference=order.order_number,
            transaction_desc=f"Payment for order {order.order_number}",
            callback_url=callback_url
        )
        
        if response.get('ResponseCode') == '0':
            payment.merchant_request_id = response.get('MerchantRequestID')
            payment.checkout_request_id = response.get('CheckoutRequestID')
            payment.status = 'processing'
            payment.save()
            
            messages.success(request, 'Payment request sent to your phone. Please enter M-Pesa PIN to complete.')
            return redirect('payment_waiting', payment_id=payment.id)
        else:
            payment.status = 'failed'
            payment.result_desc = response.get('errorMessage', 'Unknown error')
            payment.save()
            messages.error(request, f'Payment initiation failed: {response.get("errorMessage", "Unknown error")}')
    
    return render(request, 'payments/payment_form.html', {
        'order': order,
        'default_phone': request.user.phone_number
    })

@login_required
def payment_waiting(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
    return render(request, 'payments/payment_waiting.html', {'payment': payment})

@login_required
def check_payment_status(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.status == 'completed':
        return JsonResponse({'status': 'completed', 'redirect_url': payment.order.get_absolute_url()})
    elif payment.status == 'failed':
        return JsonResponse({'status': 'failed', 'message': payment.result_desc})
    
    # Query M-Pesa for status
    mpesa = MpesaAPI()
    result = mpesa.query_transaction(payment.checkout_request_id)
    
    return JsonResponse({'status': payment.status, 'result': result.get('ResultCode')})

@csrf_exempt
def mpesa_callback(request):
    if request.method != 'POST':
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        callback_data = data.get('Body', {}).get('stkCallback', {})
        
        merchant_request_id = callback_data.get('MerchantRequestID')
        checkout_request_id = callback_data.get('CheckoutRequestID')
        result_code = callback_data.get('ResultCode')
        result_desc = callback_data.get('ResultDesc')
        
        payment = Payment.objects.get(
            merchant_request_id=merchant_request_id,
            checkout_request_id=checkout_request_id
        )
        
        if result_code == 0:
            # Success
            callback_metadata = callback_data.get('CallbackMetadata', {}).get('Item', [])
            metadata_dict = {item['Name']: item.get('Value') for item in callback_metadata}
            
            payment.status = 'completed'
            payment.mpesa_receipt_number = metadata_dict.get('MpesaReceiptNumber')
            payment.transaction_date = metadata_dict.get('TransactionDate')
            payment.result_code = str(result_code)
            payment.result_desc = result_desc
            
            # Update order
            payment.order.payment_status = 'paid'
            payment.order.status = 'confirmed'
            payment.order.save()
        else:
            # Failed
            payment.status = 'failed'
            payment.result_code = str(result_code)
            payment.result_desc = result_desc
        
        payment.save()
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
    
    except Exception as e:
        return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)})

@login_required
def payment_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'payments/payment_confirmation.html', {'order': order})