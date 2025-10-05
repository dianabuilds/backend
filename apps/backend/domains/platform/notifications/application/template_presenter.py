from __future__ import annotations

from datetime import datetime
from typing import Any

from ..domain.template import Template


def _iso(value: datetime | None) -> str | None:
    return value.isoformat().replace("+00:00", "Z") if value else None


def template_to_dict(template: Template) -> dict[str, Any]:
    return {
        "id": template.id,
        "slug": template.slug,
        "name": template.name,
        "description": template.description,
        "subject": template.subject,
        "body": template.body,
        "locale": template.locale,
        "variables": template.variables or {},
        "meta": template.meta or {},
        "created_by": template.created_by,
        "created_at": _iso(template.created_at),
        "updated_at": _iso(template.updated_at),
    }


def build_list_response(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"items": items}


def build_single_response(template: Template) -> dict[str, Any]:
    return {"template": template_to_dict(template)}


def build_delete_response() -> dict[str, Any]:
    return {"ok": True}


__all__ = [
    "build_delete_response",
    "build_list_response",
    "build_single_response",
    "template_to_dict",
]
