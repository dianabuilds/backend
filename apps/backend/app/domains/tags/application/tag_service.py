from __future__ import annotations

from collections.abc import Sequence

from app.domains.tags.application.ports.tag_repo_port import ITagRepository


class TagService:
    def __init__(self, repo: ITagRepository) -> None:
        self._repo = repo

    async def get_or_create_tags(self, slugs: Sequence[str]) -> list[object]:
        items: list[object] = []
        for slug in slugs:
            tag = await self._repo.get_by_slug(slug)
            if tag is None:
                tag = await self._repo.create(slug, slug)
            items.append(tag)
        return items
