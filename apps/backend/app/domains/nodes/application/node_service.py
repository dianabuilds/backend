# mypy: ignore-errors
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.dao import NodeItemDAO, NodePatchDAO
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
from app.domains.nodes.service import validate_transition
from app.schemas.nodes_common import Status, Visibility


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
        item = await self._db.get(NodeItem, node_id)
        if not item or item.workspace_id != workspace_id:
            raise HTTPException(status_code=404, detail="Node not found")
        await NodePatchDAO.overlay(self._db, [item])
        return item

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
        item = await NodeItemDAO.create(
            self._db,
            workspace_id=workspace_id,
            type="quest",
            slug=f"quest-{uuid4().hex[:8]}",
            title="New quest",
            created_by_user_id=actor_id,
            status=Status.draft,
            visibility=Visibility.private,
            version=1,
        )

        # Синхронно создаём запись в таблице nodes с тем же идентификатором/slug,
        # чтобы элемент сразу отображался в админ-списках, работающих по таблице nodes.
        node = Node(
            workspace_id=workspace_id,
            slug=item.slug,
            title=item.title,
            author_id=actor_id,
            status=Status.draft,
            visibility=Visibility.private,
            created_by_user_id=actor_id,
            updated_by_user_id=actor_id,
        )
        self._db.add(node)
        await self._db.commit()
        item.node_id = node.id
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

        # Разрешаем обновлять только простые поля, связанные с графом
        allowed_updates: set[str] = {"slug", "title"}

        new_slug = data.get("slug")
        if new_slug is not None and new_slug != item.slug:
            # Проверяем уникальность slug среди NodeItem
            res = await self._db.execute(
                select(NodeItem).where(
                    NodeItem.slug == new_slug, NodeItem.id != item.id
                )
            )
            if res.scalar_one_or_none():
                raise HTTPException(status_code=409, detail="Slug already exists")

            # Проверяем уникальность slug среди Node
            res = await self._db.execute(select(Node).where(Node.slug == new_slug))
            existing_node = res.scalar_one_or_none()
            if existing_node and existing_node.id != item.node_id:
                raise HTTPException(status_code=409, detail="Slug already exists")

            item.slug = str(new_slug)

        for key, value in data.items():
            if key in allowed_updates - {"slug"}:
                setattr(item, key, value)

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
            # синхронизируем slug, если он менялся
            if new_slug is not None:
                node.slug = item.slug

        # синхронизируем заголовок, если он менялся
        if "title" in data and data["title"]:
            node.title = str(data["title"])

        # Любое редактирование опубликованной записи переводит её в черновик
        if item.status == Status.published:
            item.status = Status.draft
            item.visibility = Visibility.private
            item.published_at = None
            # согласуем видимость и статус в Node
            node.visibility = Visibility.private
            node.status = Status.draft

        node.updated_by_user_id = actor_id
        node.updated_at = datetime.utcnow()
        item.updated_by_user_id = actor_id
        item.updated_at = datetime.utcnow()

        await self._db.commit()
        return item

    async def publish(
        self,
        workspace_id: UUID | None,
        node_id: int,
        *,
        actor_id: UUID,
        access: Literal["everyone", "premium_only", "early_access"] = "everyone",
    ) -> NodeItem:
        item = await self.get(workspace_id, node_id)
        validate_transition(item.status, Status.published)

        # Обновляем состояние контентного элемента
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
        node.updated_by_user_id = actor_id
        node.updated_at = datetime.utcnow()

        await self._db.commit()
        return item
