# mypy: ignore-errors
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

import logging

from fastapi import HTTPException
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


class NodeService:
    """Service layer for managing graph nodes."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service."""

        self._db = db

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
        raw = data.get("tags") or data.get("tagSlugs") or data.get("tag_slugs")
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
        if not tags:
            return False

        res = await self._db.execute(
            select(Tag.slug)
            .join(ContentTag, Tag.id == ContentTag.tag_id)
            .where(ContentTag.content_id == item.id)
        )
        current_slugs = set(res.scalars().all())
        if current_slugs == set(tags):
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
        node = Node(
            workspace_id=workspace_id,
            # slug генерируется по умолчанию (hex) через Node.generate_slug
            title="New quest",
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
            # синхронизируем slug c Node (hex-значение)
            slug=node.slug,
            title=node.title,
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
        item = await self.get(workspace_id, node_id)

        changed = False

        new_slug = data.get("slug")
        if new_slug is not None and new_slug != item.slug:
            # Нормализуем/валидируем slug: требуем 16-символьный hex без префиксов
            import re as _re

            from app.domains.nodes.infrastructure.models.node import (
                generate_slug as _gen,
            )

            candidate = str(new_slug or "").strip().lower()
            # Игнорируем нестандартные значения (например, "quest-xxxx")
            if not _re.fullmatch(r"[a-f0-9]{16}", candidate):
                candidate = _gen()

            # Проверяем уникальность slug среди NodeItem
            res = await self._db.execute(
                select(NodeItem).where(
                    NodeItem.slug == candidate, NodeItem.id != item.id
                )
            )
            if res.scalar_one_or_none():
                raise HTTPException(status_code=409, detail="Slug already exists")

            # Проверяем уникальность slug среди Node
            res = await self._db.execute(select(Node).where(Node.slug == candidate))
            existing_node = res.scalar_one_or_none()
            if existing_node and existing_node.id != item.node_id:
                raise HTTPException(status_code=409, detail="Slug already exists")

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
        if "nodes" in data:
            logger.warning("Received legacy 'nodes' field in update payload")
            raise HTTPException(
                status_code=422,
                detail="Field 'nodes' is deprecated; use 'content' instead",
            )
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

        cover_url = data.get("cover_url", data.get("coverUrl"))
        if ("cover_url" in data or "coverUrl" in data) and cover_url != node.cover_url:
            node.cover_url = cover_url  # type: ignore[assignment]
            changed = True

        media = data.get("media")
        if media is not None and media != node.media:
            node.media = list(media)
            changed = True

        tag_slugs = self._normalize_tags(data)
        tags_changed = await self._sync_tags(item=item, node=node, tags=tag_slugs)
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
        # Обновим объект, чтобы отдать актуальные связи
        try:
            await self._db.refresh(item)
        except Exception:
            pass

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
