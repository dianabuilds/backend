from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.domains.nodes.application.ports.tag_sync_port import ITagSyncService
from app.domains.nodes.dao import NodeItemDAO
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
from app.domains.tags.models import ContentTag, Tag


class TagSyncService(ITagSyncService):
    def normalize(self, data: dict[str, Any]) -> list[str] | None:
        raw = data.get("tags")
        if not isinstance(raw, (list, tuple)):
            return None
        slugs: list[str] = []
        for t in raw:
            if isinstance(t, str):
                s = t.strip().lower()
            elif isinstance(t, dict):
                s = str(t.get("slug") or t.get("value") or t.get("id") or "").strip().lower()
            else:
                continue
            if s and s not in slugs:
                slugs.append(s)
        return slugs

    async def sync(
        self, db: AsyncSession, *, item: NodeItem, node: Node, tags: list[str] | None
    ) -> bool:
        try:
            res = await db.execute(
                select(Tag).join(ContentTag, Tag.id == ContentTag.tag_id).where(
                    ContentTag.content_id == item.id
                )
            )
            existing_tags = list(res.scalars().all())
        except Exception:
            existing_tags = []
        current_slugs = {t.slug for t in existing_tags}

        if not tags:
            set_committed_value(node, "tags", existing_tags)
            node.tags = existing_tags
            set_committed_value(item, "tags", existing_tags)
            return False

        if current_slugs == set(tags):
            set_committed_value(node, "tags", existing_tags)
            node.tags = existing_tags
            set_committed_value(item, "tags", existing_tags)
            return False

        existing: dict[str, Tag] = {}
        try:
            res = await db.execute(select(Tag).where(Tag.slug.in_(tags)))
            existing = {t.slug: t for t in res.scalars().all()}
        except Exception:
            existing = {}

        tag_objs: list[Tag] = []
        for slug in tags:
            tag = existing.get(slug)
            if tag is None:
                tag = Tag(slug=slug, name=slug)
                db.add(tag)
                await db.flush()
            tag_objs.append(tag)

        set_committed_value(node, "tags", [])
        node.tags = tag_objs
        try:
            await db.execute(delete(ContentTag).where(ContentTag.content_id == item.id))
        except Exception:
            pass
        for t in tag_objs:
            try:
                await NodeItemDAO.attach_tag(db, node_id=item.id, tag_id=t.id)
            except Exception:
                pass
        set_committed_value(item, "tags", tag_objs)
        return True


__all__ = ["TagSyncService"]

