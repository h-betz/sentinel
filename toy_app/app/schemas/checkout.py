from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class CheckoutItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=100)


class CheckoutRequest(BaseModel):
    customer_email: EmailStr
    customer_name: str = Field(min_length=1, max_length=200)
    items: list[CheckoutItem] = Field(min_length=1)
    card_token: str = Field(min_length=1)


class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal

    class Config:
        from_attributes = True


class CheckoutResponse(BaseModel):
    order_id: int
    order_number: str
    customer_email: str
    customer_name: str
    status: str
    items: list[OrderItemResponse]
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    payment_id: str | None = None
    paid_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True
