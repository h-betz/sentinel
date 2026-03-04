from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from toy_app.app.schemas.category import CategoryResponse


class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    price: Decimal
    stock_quantity: int
    image_url: str | None = None
    category: CategoryResponse

    class Config:
        from_attributes = True


class ProductDetailResponse(BaseModel):
    id: int
    sku: str
    name: str
    description: str | None = None
    price: Decimal
    stock_quantity: int
    image_url: str | None = None
    category: CategoryResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
