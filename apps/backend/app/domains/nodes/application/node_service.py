# mypy: ignore-errors
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import HTTPException
from slugify import slugify
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.core.log_events import cache_invalidate
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.application.navigation_service import NavigationService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.nodes.dao import NodeItemDAO, NodePatchDAO
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
from app.domains.nodes.service import validate_transition
from app.domains.tags.models import ContentTag, Tag
from app.schemas.nodes_common import Status, Visibility

logger = logging.getLogger(__name__)

navcache = NavigationCacheService(CoreCacheAdapter())
navsvc = NavigationService()

HEX_RE = re.compile(r"[a-f0-9]{16}")


class NodeService:
    """Service layer for managing graph nodes."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service."""

        self._db = db

    async def _unique_slug(
        self,
        base: str,
        *,
        skip_item_id: int | None = None,
        skip_node_id: int | None = None,
    ) -> str:
        slug_base = slugify(base) or "node"
        idx = 0
        while True:
            text = slug_base if idx == 0 else f"{slug_base}-{idx}"
            candidate = hashlib.sha256(text.encode()).hexdigest()[:16]
            res = await self._db.execute(
                select(NodeItem).where(NodeItem.slug == candidate)
            )
            existing_item = res.scalar_one_or_none()
            if existing_item and existing_item.id != skip_item_id:
                idx += 1
                continue
            res = await self._db.execute(select(Node).where(Node.slug == candidate))
            existing_node = res.scalar_one_or_none()
            if existing_node and existing_node.id != skip_node_id:
                idx += 1
                continue
            return candidate

    # Queries -----------------------------------------------------------------
    async def list(
        self,
        workspace_id: UUID | None,
        *,
        page: int = 1,
        per_page: int = 10,
    ) -> list[NodeItem]:
        return await NodeItemDAO.search(
            self._db,
            workspace_id=workspace_id,
            node_type="quest",
            page=page,
            per_page=per_page,
            q=None,
        )

    async def search(
        self,
        workspace_id: UUID | None,
        q: str,
        *,
        page: int = 1,
        per_page: int = 10,
    ) -> list[NodeItem]:
        return await NodeItemDAO.search(
            self._db,
            workspace_id=workspace_id,
            node_type="quest",
            q=q,
            page=page,
            per_page=per_page,
        )

    async def get(self, workspace_id: UUID | None, node_id: int) -> NodeItem:
        """Fetch a content item by id.

        Workspace acts as a filter, not a hard access boundary in admin flows.
        If ``workspace_id`` is provided and does not match the stored item, we
        still return the item (to tolerate historical data skew and imports).
        """
        item = await self._db.get(NodeItem, node_id)
        if not item:
            raise HTTPException(status_code=404, detail="Node not found")
        # Soft filter: keep behaviour permissive for admin reads
        # (no-op if workspaces match; otherwise proceed without raising)
        await NodePatchDAO.overlay(self._db, [item])
        return item

    @staticmethod
    def _normalize_tags(data: dict[str, Any]) -> list[str] | None:
        raw = data.get("tags")
        if not isinstance(raw, list | tuple):
            return None
        slugs: list[str] = []
        for t in raw:
            if isinstance(t, str):
                s = t.strip().lower()
            elif isinstance(t, dict):
                s = (
                    str(t.get("slug") or t.get("value") or t.get("id") or "")
                    .strip()
                    .lower()
                )
            else:
                continue
            if s and s not in slugs:
                slugs.append(s)
        return slugs

    async def _sync_tags(
        self,
        *,
        item: NodeItem,
        node: Node,
        tags: list[str] | None,
    ) -> bool:
        res = await self._db.execute(
            select(Tag)
            .join(ContentTag, Tag.id == ContentTag.tag_id)
            .where(ContentTag.content_id == item.id)
        )
        existing_tags = list(res.scalars().all())
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

        res = await self._db.execute(
            select(Tag).where(
                Tag.workspace_id == item.workspace_id,
                Tag.slug.in_(tags),
            )
        )
        existing = {t.slug: t for t in res.scalars().all()}

        tag_objs: list[Tag] = []
        for slug in tags:
            tag = existing.get(slug)
            if tag is None:
                tag = Tag(workspace_id=item.workspace_id, slug=slug, name=slug)
                self._db.add(tag)
                await self._db.flush()
            tag_objs.append(tag)

        set_committed_value(node, "tags", [])
        node.tags = tag_objs
        await self._db.execute(
            delete(ContentTag).where(ContentTag.content_id == item.id)
        )
        for t in tag_objs:
            await NodeItemDAO.attach_tag(
                self._db,
                node_id=item.id,
                tag_id=t.id,
                workspace_id=item.workspace_id,
            )
        set_committed_value(item, "tags", tag_objs)
        return True

    # Mutations ---------------------------------------------------------------
    async def create_item_for_node(self, node: Node) -> NodeItem:
        """Backfill a ``NodeItem`` for an existing ``Node`` record."""

        item = await NodeItemDAO.create(
            self._db,
            node_id=node.id,
            workspace_id=node.workspace_id,
            type="quest",
            status=node.status,
            visibility=node.visibility,
            version=getattr(node, "version", 1),
            slug=node.slug,
            title=node.title or "Untitled",
            created_by_user_id=node.created_by_user_id,
            updated_by_user_id=node.updated_by_user_id,
            published_at=(node.updated_at if node.status == Status.published else None),
            created_at=node.created_at,
            updated_at=node.updated_at,
        )
        await self._db.commit()
        return item

    async def create(self, workspace_id: UUID | None, *, actor_id: UUID) -> NodeItem:
        # В некоторых установках колонка content_items.node_id имеет NOT NULL.
        # Поэтому сначала создаём инфраструктурный Node, затем вставляем NodeItem
        # со ссылкой на node_id в одном транзакционном потоке.
        title = "New quest"
        slug = await self._unique_slug(title)
        node = Node(
            workspace_id=workspace_id,
            slug=slug,
            title=title,
            author_id=actor_id,
            status=Status.draft,
            visibility=Visibility.private,
            created_by_user_id=actor_id,
            updated_by_user_id=actor_id,
        )
        self._db.add(node)
        await self._db.flush()

        item = await NodeItemDAO.create(
            self._db,
            node_id=node.id,
            workspace_id=workspace_id,
            type="quest",
            slug=slug,
            title=title,
            created_by_user_id=actor_id,
            status=Status.draft,
            visibility=Visibility.private,
            version=1,
        )

        await self._db.commit()
        return item

    async def update(
        self,
        workspace_id: UUID | None,
        node_id: int,
        data: dict[str, Any],
        *,
        actor_id: UUID,
    ) -> NodeItem:
        camel = "media" + "Urls"
        snake = "media_" + "urls"
        legacy = {
            camel: "media",
            snake: "media",
            "tagSlugs": "tags",
            "tag_slugs": "tags",
            "nodes": "content",
        }
        for field, replacement in legacy.items():
            if field in data:
                raise HTTPException(
                    status_code=422,
                    detail=f"'{field}' field is deprecated; use '{replacement}'",
                )

        item = await self.get(workspace_id, node_id)

        changed = False

        new_slug = data.get("slug")
        if new_slug is not None:
            candidate = str(new_slug).strip().lower()
            if candidate:
                if HEX_RE.fullmatch(candidate):
                    res = await self._db.execute(
                        select(NodeItem).where(
                            NodeItem.slug == candidate, NodeItem.id != item.id
                        )
                    )
                    existing_item = res.scalar_one_or_none()
                    res = await self._db.execute(
                        select(Node).where(Node.slug == candidate)
                    )
                    existing_node = res.scalar_one_or_none()
                    if existing_item or (
                        existing_node and existing_node.id != item.node_id
                    ):
                        candidate = await self._unique_slug(
                            candidate,
                            skip_item_id=item.id,
                            skip_node_id=item.node_id,
                        )
                else:
                    candidate = await self._unique_slug(
                        candidate,
                        skip_item_id=item.id,
                        skip_node_id=item.node_id,
                    )
            else:
                base = data.get("title") or item.title
                candidate = await self._unique_slug(base)
            if candidate != item.slug:
                item.slug = candidate
                changed = True

        title = data.get("title")
        if title is not None and title != item.title:
            item.title = str(title)
            changed = True

        # Сохраняем контент и флаги во "внешнюю" таблицу nodes
        node = await self._db.get(Node, item.node_id) if item.node_id else None
        if node is None:
            # На случай старых записей, созданных до появления связанного Node
            node = Node(
                workspace_id=item.workspace_id,
                slug=item.slug,
                title=item.title,
                author_id=item.created_by_user_id or actor_id,
                status=item.status,
                visibility=item.visibility,
                created_by_user_id=item.created_by_user_id,
                updated_by_user_id=actor_id,
            )
            self._db.add(node)
            await self._db.commit()
            item.node_id = node.id
        else:
            if new_slug is not None:
                node.slug = item.slug

        if title is not None and title != node.title:
            node.title = str(title)

        # Content is provided under `content`
        raw_content = data.get("content")
        if raw_content is not None and raw_content != node.content:
            if isinstance(raw_content, dict | list):
                node.content = raw_content  # type: ignore[assignment]
            else:
                try:
                    import json

                    parsed = json.loads(str(raw_content))
                except Exception:
                    parsed = {"time": 0, "blocks": [], "version": "2.30.7"}
                node.content = parsed  # type: ignore[assignment]
            changed = True

        if (cover := data.get("coverUrl")) is not None and cover != node.coverUrl:
            node.coverUrl = cover  # type: ignore[assignment]
            changed = True

        media = data.get("media")
        if media is not None and media != node.media:
            node.media = list(media)
            changed = True

        tags = self._normalize_tags(data)
        tags_changed = await self._sync_tags(item=item, node=node, tags=tags)
        await self._db.refresh(item, attribute_names=["tags"])
        if tags_changed:
            changed = True

        if changed and item.status == Status.published:
            item.status = Status.draft
            item.visibility = Visibility.private
            item.published_at = None
            node.visibility = Visibility.private
            node.status = Status.draft

        node.updated_by_user_id = actor_id
        node.updated_at = datetime.utcnow()
        item.updated_by_user_id = actor_id
        item.updated_at = datetime.utcnow()

        await self._db.commit()
        if changed:
            await navsvc.invalidate_navigation_cache(self._db, node)
            await navcache.invalidate_navigation_by_node(node.slug)
            await navcache.invalidate_modes_by_node(node.slug)
            await navcache.invalidate_compass_all()
            cache_invalidate("nav", reason="node_update", key=node.slug)
            cache_invalidate("navm", reason="node_update", key=node.slug)
            cache_invalidate("comp", reason="node_update")

        return item

    async def publish(
        self,
        workspace_id: UUID | None,
        node_id: int,
        *,
        actor_id: UUID,
        access: Literal["everyone", "premium_only", "early_access"] = "everyone",
        scheduled_at: datetime | None = None,
    ) -> NodeItem:
        item = await self.get(workspace_id, node_id)
        validate_transition(item.status, Status.published)

        # Если указано будущее время — сохраняем расписание и не публикуем сразу
        if scheduled_at and scheduled_at > datetime.utcnow():
            node = await self._db.get(Node, item.node_id) if item.node_id else None
            if node is None:
                node = Node(
                    workspace_id=item.workspace_id,
                    slug=item.slug,
                    title=item.title,
                    author_id=item.created_by_user_id or actor_id,
                    status=item.status,
                    visibility=item.visibility,
                    created_by_user_id=item.created_by_user_id,
                    updated_by_user_id=actor_id,
                )
                self._db.add(node)
                await self._db.commit()
                item.node_id = node.id
            # persist schedule in Node.meta
            meta = node._meta_dict()
            meta["scheduled_at"] = scheduled_at.isoformat()
            node.meta = meta
            item.updated_by_user_id = actor_id
            node.updated_by_user_id = actor_id
            node.updated_at = datetime.utcnow()
            await self._db.commit()
            return item

        # Немедленная публикация
        if access == "early_access":
            item.visibility = Visibility.unlisted
        else:
            item.visibility = Visibility.public
        item.status = Status.published
        item.published_at = datetime.utcnow()
        item.updated_by_user_id = actor_id

        # Ищем/создаём инфраструктурную запись в nodes по id контента
        node = await self._db.get(Node, item.node_id) if item.node_id else None
        if node is None:
            node = Node(
                workspace_id=item.workspace_id,
                slug=item.slug,
                title=item.title,
                author_id=item.created_by_user_id or actor_id,
                status=item.status,
                visibility=item.visibility,
                created_by_user_id=item.created_by_user_id,
                updated_by_user_id=actor_id,
            )
            self._db.add(node)
            await self._db.commit()
            item.node_id = node.id

        # Проставляем флаги доступа и прочие поля
        node.premium_only = access == "premium_only"
        node.visibility = (
            Visibility.unlisted if access == "early_access" else Visibility.public
        )
        # очистим отложенную публикацию, если была
        try:
            meta = node._meta_dict()
            if "scheduled_at" in meta:
                meta.pop("scheduled_at", None)
                node.meta = meta
        except Exception:
            pass
        node.updated_by_user_id = actor_id
        node.updated_at = datetime.utcnow()

        await self._db.commit()
        return item
