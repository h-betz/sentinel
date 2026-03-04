from fastapi import APIRouter

from toy_app.app.dependencies import CheckoutServiceDep, ProductRepositoryDep
from toy_app.app.schemas.checkout import (
    CheckoutRequest,
    CheckoutResponse,
    OrderItemResponse,
)

router = APIRouter()


@router.post("/checkout", response_model=CheckoutResponse)
async def process_checkout(
    request: CheckoutRequest,
    checkout_service: CheckoutServiceDep,
    product_repo: ProductRepositoryDep,
) -> CheckoutResponse:
    """
    Process a checkout request.

    This endpoint has an intentional bug in the payment client that causes
    failures when the payment service returns errors, rate limits, or malformed responses.

    Request body:
    - customer_email: Valid email address
    - customer_name: Customer's full name
    - items: List of {product_id, quantity}
    - card_token: Payment card token
    """
    # Convert request items to (product_id, quantity) tuples
    items = [(item.product_id, item.quantity) for item in request.items]

    # Process checkout
    order = await checkout_service.process_checkout(
        customer_email=request.customer_email,
        customer_name=request.customer_name,
        items=items,
        card_token=request.card_token,
    )

    # Fetch product names for response
    product_ids = [item.product_id for item in order.items]
    products = await product_repo.get_products_by_ids(product_ids)
    product_map = {p.id: p for p in products}

    # Build response
    order_items = []
    for item in order.items:
        product = product_map.get(item.product_id)
        order_items.append(
            OrderItemResponse(
                product_id=item.product_id,
                product_name=product.name if product else "Unknown",
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
            )
        )

    return CheckoutResponse(
        order_id=order.id,
        order_number=order.order_number,
        customer_email=order.customer_email,
        customer_name=order.customer_name,
        status=order.status.value,
        items=order_items,
        subtotal=order.subtotal,
        tax=order.tax,
        total=order.total,
        payment_id=order.payment_id,
        paid_at=order.paid_at,
        created_at=order.created_at,
    )
