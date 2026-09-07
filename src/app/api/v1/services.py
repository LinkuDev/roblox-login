from __future__ import annotations

from fastapi import APIRouter

from app.schemas.order import ServiceInfo
from app.services import list_services

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceInfo])
def catalog():
    return [
        ServiceInfo(
            id=s.id,
            name=s.name,
            category=s.category,
            price_points=s.price_points,
            description=s.description,
            input_fields=list(s.input_fields),
        )
        for s in list_services()
    ]
