from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    billing,
    cms,
    dashboard,
    notifications,
    orders,
    pool,
    services,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(services.router)
api_router.include_router(orders.router)
api_router.include_router(billing.router)
api_router.include_router(pool.router)
api_router.include_router(dashboard.router)
api_router.include_router(notifications.router)
api_router.include_router(cms.router)
api_router.include_router(admin.router)

__all__ = ["api_router"]
