from __future__ import annotations

from app.core.registry import Registry
from app.services.base import Service, ServiceSpec

service_registry: Registry[Service] = Registry("service")


def build_service(service_id: str) -> Service:
    return service_registry.get(service_id)()


def get_service_spec(service_id: str) -> ServiceSpec:
    return service_registry.get(service_id).spec


def list_services() -> list[ServiceSpec]:
    return [service_registry.get(name).spec for name in service_registry.names()]
