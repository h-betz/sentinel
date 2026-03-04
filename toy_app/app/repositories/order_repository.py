import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from toy_app.app.models.order import Order, OrderStatus
from toy_app.app.models.order_item import OrderItem
from toy_app.app.models.product import Product


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_order(
        self,
        customer_email: str,
        customer_name: str,
        items: list[tuple[Product, int]],  # (product, quantity)
        tax_rate: Decimal = Decimal("0.08"),
    ) -> Order:
        """Create a new order with items."""
        # Generate order number
        order_number = f"ORD-{uuid.uuid4().hex[:12].upper()}"

        # Calculate totals
        subtotal = Decimal("0")
        order_items = []

        for product, quantity in items:
            unit_price = product.price
            total_price = unit_price * quantity
            subtotal += total_price

            order_item = OrderItem(
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
            )
            order_items.append(order_item)

        tax = subtotal * tax_rate
        total = subtotal + tax

        # Create order
        order = Order(
            order_number=order_number,
            customer_email=customer_email,
            customer_name=customer_name,
            status=OrderStatus.PENDING,
            subtotal=subtotal,
            tax=tax.quantize(Decimal("0.01")),
            total=total.quantize(Decimal("0.01")),
            items=order_items,
        )

        self.session.add(order)
        await self.session.flush()

        return order

    async def get_order_by_id(self, order_id: int) -> Order | None:
        """Get order by ID with items."""
        query = (
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_order_by_number(self, order_number: str) -> Order | None:
        """Get order by order number."""
        query = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.order_number == order_number)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_order_status(
        self,
        order: Order,
        status: OrderStatus,
        payment_id: str | None = None,
    ) -> Order:
        """Update order status and optionally set payment info."""
        order.status = status
        if payment_id:
            order.payment_id = payment_id
        if status == OrderStatus.PAID:
            order.paid_at = datetime.now(timezone.utc)

        return order

    async def mark_order_failed(self, order: Order, reason: str | None = None) -> Order:
        """Mark an order as failed."""
        order.status = OrderStatus.FAILED
        return order
