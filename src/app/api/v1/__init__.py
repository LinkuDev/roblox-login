from fastapi import APIRouter

from app.api.v1 import auth, billing, orders, services

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(services.router)
api_router.include_router(orders.router)
api_router.include_router(billing.router)

__all__ = ["api_router"]
