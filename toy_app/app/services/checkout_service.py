from decimal import Decimal

from fastapi import HTTPException

from toy_app.app.models.order import Order, OrderStatus
from toy_app.app.models.product import Product
from toy_app.app.repositories.order_repository import OrderRepository
from toy_app.app.repositories.product_repository import ProductRepository
from toy_app.app.services.payment_client import PaymentClient


class CheckoutError(Exception):
    """Base exception for checkout errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CheckoutService:
    def __init__(
        self,
        product_repository: ProductRepository,
        order_repository: OrderRepository,
        payment_client: PaymentClient,
    ):
        self.product_repo = product_repository
        self.order_repo = order_repository
        self.payment_client = payment_client

    async def process_checkout(
        self,
        customer_email: str,
        customer_name: str,
        items: list[tuple[int, int]],  # (product_id, quantity)
        card_token: str,
    ) -> Order:
        """
        Process a checkout request.

        Steps:
        1. Validate products exist and have sufficient stock
        2. Create order in pending state
        3. Process payment
        4. Update order status based on payment result
        5. Deduct stock on success
        """
        # Step 1: Validate products and stock
        product_ids = [item[0] for item in items]
        products = await self.product_repo.get_products_by_ids(product_ids)

        # Build product map for quick lookup
        product_map: dict[int, Product] = {p.id: p for p in products}

        # Validate all products exist
        missing_ids = set(product_ids) - set(product_map.keys())
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Products not found: {missing_ids}",
            )

        # Validate stock availability
        order_items: list[tuple[Product, int]] = []
        for product_id, quantity in items:
            product = product_map[product_id]
            if product.stock_quantity < quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for product {product.name}. "
                    f"Available: {product.stock_quantity}, Requested: {quantity}",
                )
            order_items.append((product, quantity))

        # Step 2: Create order
        order = await self.order_repo.create_order(
            customer_email=customer_email,
            customer_name=customer_name,
            items=order_items,
        )

        # Step 3: Process payment
        # BUG: The payment_client has no error handling
        # If the payment service fails, this will crash and leave the order in pending state
        try:
            payment_result = await self.payment_client.process_payment(
                amount=order.total,
                currency="USD",
                card_token=card_token,
                order_reference=order.order_number,
            )
        except Exception as e:
            # Payment failed - mark order as failed
            await self.order_repo.mark_order_failed(order, str(e))
            raise HTTPException(
                status_code=502,
                detail=f"Payment processing failed: {str(e)}",
            )

        # Step 4: Update order status
        if payment_result.success:
            await self.order_repo.update_order_status(
                order=order,
                status=OrderStatus.PAID,
                payment_id=payment_result.payment_id,
            )

            # Step 5: Deduct stock
            for product_id, quantity in items:
                await self.product_repo.update_stock(product_id, -quantity)
        else:
            await self.order_repo.mark_order_failed(order, payment_result.error)
            raise HTTPException(
                status_code=400,
                detail=f"Payment declined: {payment_result.error}",
            )

        return order

    def calculate_order_total(
        self, items: list[tuple[Product, int]], tax_rate: Decimal = Decimal("0.08")
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Calculate subtotal, tax, and total for items."""
        subtotal = sum(product.price * quantity for product, quantity in items)
        tax = subtotal * tax_rate
        total = subtotal + tax
        return subtotal, tax.quantize(Decimal("0.01")), total.quantize(Decimal("0.01"))
