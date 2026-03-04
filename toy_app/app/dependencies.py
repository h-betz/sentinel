from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from toy_app.app.database import get_session
from toy_app.app.repositories.order_repository import OrderRepository
from toy_app.app.repositories.product_repository import ProductRepository
from toy_app.app.services.checkout_service import CheckoutService
from toy_app.app.services.payment_client import PaymentClient
from toy_app.app.services.product_service import ProductService

DBSession = Annotated[AsyncSession, Depends(get_session)]


def get_product_repository(session: DBSession) -> ProductRepository:
    return ProductRepository(session)


def get_order_repository(session: DBSession) -> OrderRepository:
    return OrderRepository(session)


def get_payment_client() -> PaymentClient:
    return PaymentClient()


def get_product_service(
    repo: Annotated[ProductRepository, Depends(get_product_repository)],
) -> ProductService:
    return ProductService(repo)


def get_checkout_service(
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    order_repo: Annotated[OrderRepository, Depends(get_order_repository)],
    payment_client: Annotated[PaymentClient, Depends(get_payment_client)],
) -> CheckoutService:
    return CheckoutService(product_repo, order_repo, payment_client)


ProductRepositoryDep = Annotated[ProductRepository, Depends(get_product_repository)]
OrderRepositoryDep = Annotated[OrderRepository, Depends(get_order_repository)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
CheckoutServiceDep = Annotated[CheckoutService, Depends(get_checkout_service)]
