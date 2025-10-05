from __future__ import annotations

from typing import Any

from .template_presenter import (
    build_delete_response,
    build_list_response,
    build_single_response,
    template_to_dict,
)
from .template_service import TemplateService


async def list_templates(
    service: TemplateService, *, limit: int = 50, offset: int = 0
) -> dict[str, Any]:
    items = await service.list(limit=limit, offset=offset)
    return build_list_response([template_to_dict(item) for item in items])


async def upsert_template(
    service: TemplateService, payload: dict[str, Any]
) -> dict[str, Any]:
    template = await service.save(payload)
    return build_single_response(template)


async def get_template(
    service: TemplateService, template_id: str
) -> dict[str, Any] | None:
    template = await service.get(template_id)
    if template is None:
        return None
    return build_single_response(template)


async def delete_template(service: TemplateService, template_id: str) -> dict[str, Any]:
    await service.delete(template_id)
    return build_delete_response()


__all__ = [
    "delete_template",
    "get_template",
    "list_templates",
    "template_to_dict",
    "upsert_template",
]
