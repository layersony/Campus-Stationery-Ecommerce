"""
IntaSend wrapper — uses the official intasend-python SDK.

Install: pip install intasend-python
Docs:    https://developers.intasend.com/docs/m-pesa-stk-push
         https://developers.intasend.com/docs/payment-status
"""
import logging

from django.conf import settings
from intasend import APIService

logger = logging.getLogger(__name__)


def _service() -> APIService:
    """Return an authenticated APIService instance."""
    service = APIService(
        token=settings.INTASEND_API_KEY,
        publishable_key=settings.INTASEND_PUBLISHABLE_KEY,
        test=getattr(settings, "INTASEND_TEST_MODE", True),
    )
    
    if hasattr(service, "session"):
        service.session.headers.update({"User-Agent": "curl/8.5.0"})
    return service


def _normalize_phone(phone: str) -> int:
    """
    Convert any Kenyan format to bare integer 2547XXXXXXXX.
    The SDK's mpesa_stk_push expects an integer, not a string.
    """
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    return int(phone)


class IntaSendAPI:
    # ------------------------------------------------------------------
    # STK Push
    # ------------------------------------------------------------------

    def stk_push(self, phone_number: str, amount: int, order_number: str, email: str = "") -> dict:
        """
        Trigger an M-Pesa STK Push via the IntaSend Python SDK.

        On success the SDK returns a dict like:
            {
                "invoice": {
                    "invoice_id": "XXXXXXX",
                    "state": "PENDING",
                    "api_ref": "<order_number>",
                    ...
                },
                ...
            }
        Raises an exception on network / auth failure — callers must catch.
        """
        # The SDK requires an email address for the customer.
        # Fall back to a configurable site-wide placeholder when the user
        # has no email set (e.g. phone-only accounts).
        customer_email = email or getattr(settings, "INTASEND_DEFAULT_EMAIL", "noreply@example.com")

        service = _service()
        response = service.collect.mpesa_stk_push(
            phone_number=_normalize_phone(phone_number),  # SDK wants an int
            email=customer_email,
            amount=int(amount),
            narrative=f"Order {order_number}",
            api_ref=order_number,   # echoed back in webhook so we can match the order
        )
        logger.debug("IntaSend STK push response: %s", response)
        return response

    # ------------------------------------------------------------------
    # Status query  (AJAX poller fallback while waiting for the webhook)
    # ------------------------------------------------------------------

    def get_invoice_status(self, invoice_id: str) -> dict:
        """
        Poll IntaSend for the current state of an invoice.

        The SDK calls POST /api/v1/payment/status/ with {"invoice_id": "..."}
        under the hood.

        !! Do NOT call GET /api/v1/payment/<id>/ directly — that endpoint
           returns an empty body and raises a JSONDecodeError. !!

        Possible invoice.state values: PENDING | PROCESSING | COMPLETE | FAILED
        """
        service = _service()
        response = service.collect.status(invoice_id=invoice_id)
        logger.debug("IntaSend status response for %s: %s", invoice_id, response)
        return response