"""
Mock Payment Service with Configurable Failure Modes.

This service simulates various failure conditions that can occur
with third-party payment processors to test error handling.

Failure Modes:
- none: Normal operation, all payments succeed
- rate_limit: Returns 429 Too Many Requests
- malformed_json: Returns invalid JSON
- missing_id: Returns valid JSON but without 'id' field
- timeout: Delays response for 60 seconds
- random: Randomly chooses a failure mode (50% success rate)
- server_error: Returns 500 Internal Server Error
"""

import asyncio
import json
import random
import uuid
from enum import Enum

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

app = FastAPI(title="Mock Payment Service")


class FailureMode(str, Enum):
    NONE = "none"
    RATE_LIMIT = "rate_limit"
    MALFORMED_JSON = "malformed_json"
    MISSING_ID = "missing_id"
    TIMEOUT = "timeout"
    RANDOM = "random"
    SERVER_ERROR = "server_error"


class PaymentRequest(BaseModel):
    amount: str
    currency: str
    card_token: str
    order_reference: str


class ConfigRequest(BaseModel):
    failure_mode: FailureMode


# Global state for failure mode
_current_failure_mode: FailureMode = FailureMode.NONE

# Track payments for status lookups
_payments: dict[str, dict] = {}


@app.get("/health")
async def health():
    return {"status": "healthy", "failure_mode": _current_failure_mode.value}


@app.post("/config/failure-mode")
async def set_failure_mode(config: ConfigRequest):
    """Set the failure mode for the payment service."""
    global _current_failure_mode
    _current_failure_mode = config.failure_mode
    return {"failure_mode": _current_failure_mode.value}


@app.get("/config/failure-mode")
async def get_failure_mode():
    """Get the current failure mode."""
    return {"failure_mode": _current_failure_mode.value}


def _get_effective_failure_mode() -> FailureMode:
    """Get the effective failure mode, resolving 'random' to a specific mode."""
    if _current_failure_mode == FailureMode.RANDOM:
        # 50% chance of success, 50% chance of various failures
        if random.random() < 0.5:
            return FailureMode.NONE
        return random.choice(
            [
                FailureMode.RATE_LIMIT,
                FailureMode.MALFORMED_JSON,
                FailureMode.MISSING_ID,
                FailureMode.SERVER_ERROR,
            ]
        )
    return _current_failure_mode


@app.post("/payments")
async def create_payment(request: Request):
    """
    Process a payment request.

    The response depends on the configured failure mode.
    """
    # Parse request body
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return Response(
            content='{"error": "Invalid JSON"}',
            status_code=400,
            media_type="application/json",
        )

    mode = _get_effective_failure_mode()

    # Handle different failure modes
    if mode == FailureMode.RATE_LIMIT:
        return Response(
            content='{"error": "Too many requests", "retry_after": 60}',
            status_code=429,
            media_type="application/json",
        )

    if mode == FailureMode.MALFORMED_JSON:
        # Return invalid JSON that will cause json.loads() to fail
        return Response(
            content='{"id": "pay_123", invalid json here...',
            status_code=200,
            media_type="application/json",
        )

    if mode == FailureMode.MISSING_ID:
        # Return valid JSON but missing the 'id' field
        return Response(
            content='{"status": "failed", "error": "Card declined", "code": "card_declined"}',
            status_code=200,
            media_type="application/json",
        )

    if mode == FailureMode.TIMEOUT:
        # Simulate a very slow response (60 seconds)
        await asyncio.sleep(60)
        payment_id = f"pay_{uuid.uuid4().hex[:16]}"
        return {"id": payment_id, "status": "succeeded"}

    if mode == FailureMode.SERVER_ERROR:
        return Response(
            content='{"error": "Internal server error", "code": "internal_error"}',
            status_code=500,
            media_type="application/json",
        )

    # Normal success case
    payment_id = f"pay_{uuid.uuid4().hex[:16]}"
    payment = {
        "id": payment_id,
        "status": "succeeded",
        "amount": body.get("amount"),
        "currency": body.get("currency", "USD"),
        "order_reference": body.get("order_reference"),
        "created_at": "2024-01-01T00:00:00Z",
    }
    _payments[payment_id] = payment

    return payment


@app.get("/payments/{payment_id}")
async def get_payment(payment_id: str):
    """Get payment status."""
    mode = _get_effective_failure_mode()

    if mode == FailureMode.RATE_LIMIT:
        return Response(
            content='{"error": "Too many requests"}',
            status_code=429,
            media_type="application/json",
        )

    if mode == FailureMode.SERVER_ERROR:
        return Response(
            content='{"error": "Internal server error"}',
            status_code=500,
            media_type="application/json",
        )

    payment = _payments.get(payment_id)
    if not payment:
        return Response(
            content='{"error": "Payment not found"}',
            status_code=404,
            media_type="application/json",
        )

    return payment


@app.post("/payments/{payment_id}/refund")
async def refund_payment(payment_id: str, request: Request):
    """Refund a payment."""
    mode = _get_effective_failure_mode()

    if mode == FailureMode.RATE_LIMIT:
        return Response(
            content='{"error": "Too many requests"}',
            status_code=429,
            media_type="application/json",
        )

    if mode == FailureMode.MALFORMED_JSON:
        return Response(
            content='{"id": "ref_123", broken...',
            status_code=200,
            media_type="application/json",
        )

    if mode == FailureMode.MISSING_ID:
        return Response(
            content='{"status": "failed", "error": "Cannot refund"}',
            status_code=200,
            media_type="application/json",
        )

    if mode == FailureMode.SERVER_ERROR:
        return Response(
            content='{"error": "Internal server error"}',
            status_code=500,
            media_type="application/json",
        )

    refund_id = f"ref_{uuid.uuid4().hex[:16]}"
    return {
        "id": refund_id,
        "payment_id": payment_id,
        "status": "succeeded",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
