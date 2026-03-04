from fastapi import APIRouter, HTTPException, Query

from toy_app.app.dependencies import ProductServiceDep
from toy_app.app.schemas.product import (
    ProductDetailResponse,
    ProductListResponse,
    ProductResponse,
)
from toy_app.app.services.product_service import ProductService

router = APIRouter()


@router.get("/products", response_model=ProductListResponse)
async def list_products(
    service: ProductServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=50, description="Items per page (max 50)"),
    category_id: int | None = Query(None, description="Filter by category ID"),
    min_price: float | None = Query(None, ge=0, description="Minimum price filter"),
    max_price: float | None = Query(None, ge=0, description="Maximum price filter"),
    in_stock: bool | None = Query(None, description="Filter by stock availability"),
    search: str | None = Query(
        None, description="Search in product name and description"
    ),
) -> ProductListResponse:
    """Get paginated list of products with optional filters."""
    result = await service.list_products(
        page=page,
        page_size=page_size,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        search=search,
    )

    # Convert to response models
    product_responses = []
    for product in result.products:
        product_responses.append(
            ProductResponse(
                id=product.id,
                sku=product.sku,
                name=product.name,
                price=product.price,
                stock_quantity=product.stock_quantity,
                image_url=product.image_url,
                category=product.category,
            )
        )

    return ProductListResponse(
        items=product_responses,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.get("/product/{product_id}", response_model=ProductDetailResponse)
async def get_product(
    product_id: int,
    service: ProductServiceDep,
) -> ProductDetailResponse:
    """Get detailed information about a specific product."""
    product = await service.get_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductDetailResponse(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        price=product.price,
        stock_quantity=product.stock_quantity,
        image_url=product.image_url,
        category=product.category,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.get("/products/debug/memory-stats")
async def get_memory_stats() -> dict:
    """
    Debug endpoint to observe the memory leak.

    Returns statistics about the accumulated cache entries.
    Watch these numbers grow as you make requests to /products.
    """
    return ProductService.get_memory_stats()


@router.post("/products/debug/clear-caches")
async def clear_caches() -> dict:
    """
    Clear the leaked caches (for testing/debugging).

    Use this to reset the memory leak counters.
    """
    return ProductService.clear_caches()
