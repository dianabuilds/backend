# mypy: ignore-errors
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.dao import NodeItemDAO, NodePatchDAO
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
from app.domains.nodes.service import validate_transition
from app.schemas.nodes_common import NodeType, Status, Visibility


class NodeService:
    """Service layer for managing graph nodes."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service."""

        self._db = db
        # Разрешаем все известные типы NodeType (по умолчанию только "quest")
        self._allowed_types = {t.value for t in NodeType}

    # ------------------------------------------------------------------
    def _normalize_type(self, node_type: str | NodeType) -> str:
        # Нормализуем вход: поддерживаем Enum, строки и распространённые алиасы
        value = node_type.value if isinstance(node_type, NodeType) else str(node_type)
        value = value.strip().lower()

        # Распространённые варианты синонимов и множественного числа
        aliases = {
            "articles": "quest",
            "article": "quest",
            "index": "quest",
            "page": "quest",
            "pages": "quest",
            "post": "quest",
            "posts": "quest",
            "story": "quest",
            "stories": "quest",
            "blog": "quest",
            "blogs": "quest",
            "news": "quest",
            "quests": "quest",
        }
        # Сначала подставим алиас, если он известен
        value = aliases.get(value, value)

        # Обработка общего случая множественного числа, если вдруг прилетит новый тип
        if value.endswith("s") and value[:-1] in self._allowed_types:
            value = value[:-1]

        # Фолбэк: любые неизвестные значения трактуем как quest,
        # чтобы не блокировать работу админки различиями терминов.
        if value not in self._allowed_types:
            value = "quest"

        return value

    # Queries -----------------------------------------------------------------
    async def list(
        self,
        workspace_id: UUID,
        node_type: str | NodeType,
        *,
        page: int = 1,
        per_page: int = 10,
    ) -> list[NodeItem]:
        node_type = self._normalize_type(node_type)
        return await NodeItemDAO.search(
            self._db,
            workspace_id=workspace_id,
            node_type=node_type,
            page=page,
            per_page=per_page,
            q=None,
        )

    async def search(
        self,
        workspace_id: UUID,
        node_type: str | NodeType,
        q: str,
        *,
        page: int = 1,
        per_page: int = 10,
    ) -> list[NodeItem]:
        node_type = self._normalize_type(node_type)
        return await NodeItemDAO.search(
            self._db,
            workspace_id=workspace_id,
            node_type=node_type,
            q=q,
            page=page,
            per_page=per_page,
        )

    async def get(
        self, workspace_id: UUID, node_type: str | NodeType, node_id: UUID
    ) -> NodeItem:
        node_type = self._normalize_type(node_type)
        item = await self._db.get(NodeItem, node_id)
        if not item or item.workspace_id != workspace_id:
            raise HTTPException(status_code=404, detail="Node not found")
        if item.type not in {node_type, "article"}:
            raise HTTPException(status_code=404, detail="Node not found")
        await NodePatchDAO.overlay(self._db, [item])
        return item

    # Mutations ---------------------------------------------------------------
    async def create(
        self, workspace_id: UUID, node_type: str | NodeType, *, actor_id: UUID
    ) -> NodeItem:
        node_type = self._normalize_type(node_type)
        # Явно задаём значения, которые в БД имеют server_default,
        # чтобы не провоцировать ленивую подгрузку и MissingGreenlet при сериализации.
        item = await NodeItemDAO.create(
            self._db,
            workspace_id=workspace_id,
            type=node_type,
            slug=f"{node_type}-{uuid4().hex[:8]}",
            title=f"New {node_type}",
            created_by_user_id=actor_id,
            status=Status.draft,
            visibility=Visibility.private,
            version=1,
        )

        # Синхронно создаём запись в таблице nodes с тем же идентификатором/slug,
        # чтобы элемент сразу отображался в админ-списках, работающих по таблице nodes.
        node = Node(
            id=item.id,  # связываем 1:1 по идентификатору
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
        # Проставляем ссылку из контентной записи на node
        item.node_id = node.id

        await self._db.commit()
        return item

    async def update(
        self,
        workspace_id: UUID,
        node_type: str | NodeType,
        node_id: UUID,
        data: dict[str, Any],
        *,
        actor_id: UUID,
    ) -> NodeItem:
        node_type = self._normalize_type(node_type)
        item = await self.get(workspace_id, node_type, node_id)

        # Разрешаем обновлять только простые поля, связанные с графом
        allowed_updates: set[str] = {
            "slug",
            "title",
        }
        for key, value in data.items():
            if key in allowed_updates:
                setattr(item, key, value)

        # Сохраняем контент и флаги во "внешнюю" таблицу nodes
        node = await self._db.get(Node, item.node_id or item.id)
        if node is None:
            # На случай старых записей, созданных до появления связанного Node
            node = Node(
                id=item.id,
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
            item.node_id = node.id

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
        workspace_id: UUID,
        node_type: str | NodeType,
        node_id: UUID,
        *,
        actor_id: UUID,
        access: Literal["everyone", "premium_only", "early_access"] = "everyone",
    ) -> NodeItem:
        node_type = self._normalize_type(node_type)
        item = await self.get(workspace_id, node_type, node_id)
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
        node = await self._db.get(Node, item.node_id or item.id)
        if node is None:
            node = Node(
                id=item.id,
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
