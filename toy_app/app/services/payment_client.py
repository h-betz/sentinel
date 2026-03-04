import time
from dataclasses import dataclass
from decimal import Decimal

import httpx

from toy_app.app.config import settings
from toy_app.app.metrics import payment_request_duration_seconds, payment_requests_total


@dataclass
class PaymentResult:
    success: bool
    payment_id: str | None = None
    error: str | None = None


class PaymentClient:
    """
    Client for communicating with the payment service.

    BUG: Third-Party Flake - No Error Handling
    This client makes several dangerous assumptions:
    1. The HTTP request will always succeed
    2. The response will always be valid JSON
    3. The JSON will always contain an 'id' field
    4. HTTP status codes are not checked

    This causes crashes when:
    - Payment service returns 429 (rate limit)
    - Payment service returns malformed JSON
    - Payment service returns error response without 'id'
    - Payment service times out
    - Network errors occur

    FIX: Add proper error handling:
    - Check response.status_code
    - Wrap response.json() in try/except
    - Validate response structure before accessing fields
    - Handle timeouts and network errors
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.payment_service_url

    async def process_payment(
        self,
        amount: Decimal,
        currency: str,
        card_token: str,
        order_reference: str,
    ) -> PaymentResult:
        """
        Process a payment through the payment service.

        BUG: No validation of HTTP status code or response structure.
        Assumes response.json()['id'] always exists and is valid.
        """
        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/payments",
                    json={
                        "amount": str(amount),
                        "currency": currency,
                        "card_token": card_token,
                        "order_reference": order_reference,
                    },
                    timeout=30.0,
                )

                # BUG: No status code check!
                # If status is 429, 500, etc., this still tries to parse JSON

                # BUG: No try/except around json parsing!
                # Malformed JSON will crash here
                data = response.json()

                # BUG: No validation that 'id' exists!
                # Error responses may not have 'id' field
                payment_id = data["id"]

                # Record success metrics
                duration = time.perf_counter() - start_time
                payment_request_duration_seconds.labels(operation="process").observe(
                    duration
                )
                payment_requests_total.labels(
                    status="success", operation="process"
                ).inc()

                return PaymentResult(
                    success=True,
                    payment_id=payment_id,
                )
        except Exception:
            # Record failure metrics
            duration = time.perf_counter() - start_time
            payment_request_duration_seconds.labels(operation="process").observe(
                duration
            )
            payment_requests_total.labels(status="error", operation="process").inc()
            raise

    async def get_payment_status(self, payment_id: str) -> dict:
        """Get the status of a payment."""
        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/payments/{payment_id}",
                    timeout=10.0,
                )
                # Same bugs as above - no error handling
                result = response.json()

                # Record success metrics
                duration = time.perf_counter() - start_time
                payment_request_duration_seconds.labels(operation="status").observe(
                    duration
                )
                payment_requests_total.labels(
                    status="success", operation="status"
                ).inc()

                return result
        except Exception:
            # Record failure metrics
            duration = time.perf_counter() - start_time
            payment_request_duration_seconds.labels(operation="status").observe(
                duration
            )
            payment_requests_total.labels(status="error", operation="status").inc()
            raise

    async def refund_payment(
        self, payment_id: str, amount: Decimal | None = None
    ) -> PaymentResult:
        """Refund a payment (full or partial)."""
        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient() as client:
                payload = {}
                if amount is not None:
                    payload["amount"] = str(amount)

                response = await client.post(
                    f"{self.base_url}/payments/{payment_id}/refund",
                    json=payload,
                    timeout=30.0,
                )
                # Same bugs - no error handling
                data = response.json()

                # Record success metrics
                duration = time.perf_counter() - start_time
                payment_request_duration_seconds.labels(operation="refund").observe(
                    duration
                )
                payment_requests_total.labels(
                    status="success", operation="refund"
                ).inc()

                return PaymentResult(
                    success=True,
                    payment_id=data["id"],
                )
        except Exception:
            # Record failure metrics
            duration = time.perf_counter() - start_time
            payment_request_duration_seconds.labels(operation="refund").observe(
                duration
            )
            payment_requests_total.labels(status="error", operation="refund").inc()
            raise
