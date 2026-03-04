from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from toy_app.app.models.category import Category
from toy_app.app.models.product import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_products(
        self,
        page: int = 1,
        page_size: int = 20,
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Product], int]:
        """Get paginated list of products with eager loading of categories."""
        # Build base query with eager loading to avoid MissingGreenlet error in async context
        query = select(Product).options(selectinload(Product.category))

        # Apply filters
        if category_id is not None:
            query = query.where(Product.category_id == category_id)
        # BUG: min_price filter is applied in-memory instead of SQL (see below)
        if max_price is not None:
            query = query.where(Product.price <= max_price)
        if in_stock is True:
            query = query.where(Product.stock_quantity > 0)
        elif in_stock is False:
            query = query.where(Product.stock_quantity == 0)

        # BUG: LIKE search on non-indexed columns causes full table scan
        # Using LIKE '%term%' cannot use B-tree indexes, resulting in sequential scan
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (Product.name.ilike(search_pattern))
                | (Product.description.ilike(search_pattern))
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Product.id)

        # Execute query
        result = await self.session.execute(query)
        products = list(result.scalars().all())

        # BUG: In-memory filtering for min_price instead of SQL WHERE clause
        # This loads ALL products into memory first, then filters in Python
        # causing O(n) memory usage and slower performance than SQL filtering
        if min_price is not None:
            products = [p for p in products if p.price >= min_price]
            total = len(products)  # Pagination totals become incorrect

        return products, total

    async def get_product_by_id(self, product_id: int) -> Product | None:
        """Get a single product by ID."""
        query = select(Product).where(Product.id == product_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_products_by_ids(self, product_ids: list[int]) -> list[Product]:
        """Get multiple products by their IDs."""
        query = select(Product).where(Product.id.in_(product_ids))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_stock(self, product_id: int, quantity_change: int) -> bool:
        """
        Update product stock quantity.
        Returns True if successful, False if insufficient stock.
        """
        product = await self.get_product_by_id(product_id)
        if not product:
            return False

        new_quantity = product.stock_quantity + quantity_change
        if new_quantity < 0:
            return False

        product.stock_quantity = new_quantity
        return True

    async def get_category_by_id(self, category_id: int) -> Category | None:
        """Get a category by ID."""
        query = select(Category).where(Category.id == category_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
