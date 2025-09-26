from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from slugify import slugify

from domains.platform.notifications.domain.template import Template
from domains.platform.notifications.ports import TemplateRepo

_ALLOWED_LOCALES = {"en", "ru"}
_DEFAULT_SLUG = "template"


class TemplateService:
    def __init__(self, repo: TemplateRepo) -> None:
        self._repo = repo

    async def list(self, limit: int = 50, offset: int = 0) -> list[Template]:
        return await self._repo.list(limit=limit, offset=offset)

    async def get(self, template_id: str) -> Template | None:
        return await self._repo.get(template_id)

    async def get_by_slug(self, slug: str) -> Template | None:
        if not slug:
            return None
        return await self._repo.get_by_slug(str(slug).strip())

    async def save(self, payload: dict[str, Any]) -> Template:
        data = dict(payload or {})
        template_id = str(data.get("id") or "").strip() or None
        data.setdefault("id", template_id)
        existing: Template | None = None
        if template_id:
            existing = await self._repo.get(template_id)
            if existing is None:
                raise ValueError("template_not_found")
        name = str(data.get("name") or (existing.name if existing else "") or "").strip()
        if not name:
            raise ValueError("name is required")
        data["name"] = name
        for key in ("variables", "meta"):
            raw_value = data.get(key)
            parsed = raw_value
            if isinstance(raw_value, str):
                stripped = raw_value.strip()
                if not stripped:
                    parsed = None
                else:
                    try:
                        parsed = json.loads(stripped)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"{key}_invalid_json") from exc
            if parsed is None:
                data[key] = None
                continue
            if not isinstance(parsed, Mapping):
                raise ValueError(f"{key}_must_be_object")
            try:
                data[key] = dict(parsed)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{key}_must_be_object") from exc
        data["slug"] = await self._prepare_slug(data, existing)
        locale_source = (
            data.get("locale") if "locale" in data else (existing.locale if existing else None)
        )
        data["locale"] = self._normalize_locale(locale_source)
        optional_fields = ("description", "subject", "locale", "variables", "meta", "created_at")
        if existing:
            data.setdefault("id", existing.id)
            if not data.get("created_by"):
                data["created_by"] = existing.created_by
            for field in optional_fields:
                if field not in data or data[field] is None:
                    data[field] = getattr(existing, field)
        else:
            for field in optional_fields + ("created_by",):
                data.setdefault(field, None)
        return await self._repo.upsert(data)

    async def delete(self, template_id: str) -> None:
        await self._repo.delete(template_id)

    async def _prepare_slug(self, data: Mapping[str, Any], existing: Template | None) -> str:
        raw = str(data.get("slug") or "").strip()
        if raw:
            base = slugify(raw, lowercase=True, separator="-")
        else:
            source = str(data.get("name") or data.get("subject") or "").strip()
            base = slugify(source, lowercase=True, separator="-")
        if not base:
            base = _DEFAULT_SLUG
        return await self._ensure_unique_slug(base, existing.id if existing else None)

    async def _ensure_unique_slug(self, base: str, exclude_id: str | None) -> str:
        candidate = base
        counter = 2
        while True:
            existing = await self._repo.get_by_slug(candidate)
            if existing is None or (exclude_id and existing.id == exclude_id):
                return candidate
            candidate = f"{base}-{counter}"
            counter += 1

    def _normalize_locale(self, locale: Any) -> str | None:
        if locale is None:
            return None
        value = str(locale).strip()
        if not value:
            return None
        normalized = value.replace("_", "-").lower()
        if normalized not in _ALLOWED_LOCALES:
            raise ValueError(f"unsupported locale '{value}'")
        return normalized


__all__ = ["TemplateService"]
