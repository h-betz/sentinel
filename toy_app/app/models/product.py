from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from toy_app.app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from toy_app.app.models.category import Category


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(default=0, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False
    )

    # BUG: Using lazy loading (default) instead of eager loading
    # This causes N+1 queries when listing products with categories
    category: Mapped["Category"] = relationship("Category", back_populates="products")
