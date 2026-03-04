import time
from dataclasses import dataclass

from toy_app.app.metrics import (
    estimated_leak_memory_bytes,
    product_analytics_entries,
    product_cache_entries,
)
from toy_app.app.models.product import Product
from toy_app.app.repositories.product_repository import ProductRepository

# BUG: Memory Leak - Global caches that grow unbounded
# These dictionaries/lists accumulate data forever and are never cleaned up

# Cache using timestamp-based keys means infinite unique keys
_product_view_cache: dict[str, dict] = {}

# Analytics list that grows with every product view
_product_analytics: list[dict] = []


@dataclass
class ProductListResult:
    products: list[Product]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    async def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock: bool | None = None,
        search: str | None = None,
    ) -> ProductListResult:
        """
        List products with pagination and filtering.

        BUG: Memory Leak
        Each call to this method adds data to global caches that are never cleaned.
        The _product_view_cache uses timestamp-based keys, creating infinite entries.
        The _product_analytics list grows unbounded.
        """
        # Enforce max page size
        page_size = min(page_size, 50)

        products, total = await self.repository.get_products(
            page=page,
            page_size=page_size,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
            search=search,
        )

        # BUG: Cache with timestamp-based key creates infinite unique entries
        cache_key = f"list_{page}_{page_size}_{time.time_ns()}"
        _product_view_cache[cache_key] = {
            "page": page,
            "page_size": page_size,
            "filters": {
                "category_id": category_id,
                "min_price": min_price,
                "max_price": max_price,
                "in_stock": in_stock,
            },
            "result_count": len(products),
            "timestamp": time.time(),
            # ~1KB of padding data per entry to make leak more visible
            "debug_data": "x" * 1024,
        }

        # BUG: Analytics list grows unbounded
        _product_analytics.append(
            {
                "action": "list_products",
                "page": page,
                "page_size": page_size,
                "result_count": len(products),
                "timestamp": time.time(),
                # Additional data to increase memory footprint
                "request_metadata": {
                    "filters_applied": bool(
                        category_id or min_price or max_price or in_stock
                    ),
                    "debug_trace": "x" * 512,
                },
            }
        )

        # Update Prometheus metrics for memory leak detection
        self._update_memory_metrics()

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return ProductListResult(
            products=products,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_product(self, product_id: int) -> Product | None:
        """
        Get a single product by ID.

        BUG: Memory Leak (same as list_products)
        """
        product = await self.repository.get_product_by_id(product_id)

        if product:
            # BUG: More unbounded cache growth
            cache_key = f"product_{product_id}_{time.time_ns()}"
            _product_view_cache[cache_key] = {
                "product_id": product_id,
                "product_name": product.name,
                "timestamp": time.time(),
                "debug_data": "x" * 1024,
            }

            _product_analytics.append(
                {
                    "action": "view_product",
                    "product_id": product_id,
                    "product_name": product.name,
                    "timestamp": time.time(),
                    "debug_trace": "x" * 512,
                }
            )

            # Update Prometheus metrics for memory leak detection
            self._update_memory_metrics()

        return product

    @staticmethod
    def _update_memory_metrics() -> None:
        """Update Prometheus gauges for memory leak metrics."""
        cache_size = len(_product_view_cache)
        analytics_size = len(_product_analytics)

        product_cache_entries.set(cache_size)
        product_analytics_entries.set(analytics_size)

        # Estimate memory in bytes
        cache_memory_bytes = cache_size * 1536  # ~1.5KB per entry
        analytics_memory_bytes = analytics_size * 768  # ~0.75KB per entry
        estimated_leak_memory_bytes.set(cache_memory_bytes + analytics_memory_bytes)

    @staticmethod
    def get_memory_stats() -> dict:
        """
        Debug endpoint to observe memory leak.
        Returns statistics about the leaked memory.
        """
        cache_size = len(_product_view_cache)
        analytics_size = len(_product_analytics)

        # Estimate memory usage (rough calculation)
        cache_memory_kb = cache_size * 1.5  # ~1.5KB per entry
        analytics_memory_kb = analytics_size * 0.75  # ~0.75KB per entry
        total_memory_kb = cache_memory_kb + analytics_memory_kb

        # Update Prometheus metrics
        product_cache_entries.set(cache_size)
        product_analytics_entries.set(analytics_size)
        estimated_leak_memory_bytes.set(total_memory_kb * 1024)

        return {
            "cache_entries": cache_size,
            "analytics_entries": analytics_size,
            "estimated_cache_memory_kb": round(cache_memory_kb, 2),
            "estimated_analytics_memory_kb": round(analytics_memory_kb, 2),
            "estimated_total_memory_kb": round(total_memory_kb, 2),
            "estimated_total_memory_mb": round(total_memory_kb / 1024, 2),
        }

    @staticmethod
    def clear_caches() -> dict:
        """Clear the leaked caches (for testing purposes)."""
        global _product_view_cache, _product_analytics
        old_cache_size = len(_product_view_cache)
        old_analytics_size = len(_product_analytics)

        _product_view_cache = {}
        _product_analytics = []

        return {
            "cleared_cache_entries": old_cache_size,
            "cleared_analytics_entries": old_analytics_size,
        }
