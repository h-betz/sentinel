from fastapi import APIRouter

from toy_app.app.api.checkout import router as checkout_router
from toy_app.app.api.products import router as products_router

api_router = APIRouter()

api_router.include_router(products_router, tags=["products"])
api_router.include_router(checkout_router, tags=["checkout"])
