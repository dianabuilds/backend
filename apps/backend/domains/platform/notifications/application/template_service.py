from __future__ import annotations

from typing import Any

from domains.platform.notifications.domain.template import Template
from domains.platform.notifications.ports import TemplateRepo


class TemplateService:
    def __init__(self, repo: TemplateRepo) -> None:
        self._repo = repo

    async def list(self, limit: int = 50, offset: int = 0) -> list[Template]:
        return await self._repo.list(limit=limit, offset=offset)

    async def get(self, template_id: str) -> Template | None:
        return await self._repo.get(template_id)

    async def save(self, payload: dict[str, Any]) -> Template:
        data = dict(payload)
        slug = data.get("slug")
        if not slug:
            raise ValueError("slug is required")
        template_id = data.get("id")
        if template_id:
            existing = await self._repo.get(template_id)
        else:
            existing = await self._repo.get_by_slug(str(slug))
            if existing:
                data["id"] = existing.id
        if existing and not data.get("created_by"):
            data["created_by"] = existing.created_by
        return await self._repo.upsert(data)

    async def delete(self, template_id: str) -> None:
        await self._repo.delete(template_id)


__all__ = ["TemplateService"]
