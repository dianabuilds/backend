from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log_events import cache_invalidate
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.application.traces_service import TracesService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.nodes.dao import NodeItemDAO, NodePatchDAO
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
from app.domains.nodes.service import publish_content, validate_transition
from app.domains.quests.application.editor_service import EditorService
from app.domains.telemetry.application.audit_service import AuditService
from app.domains.telemetry.infrastructure.repositories.audit_repository import (
    AuditLogRepository,
)
from app.domains.users.infrastructure.models.user import User
from app.schemas.nodes_common import NodeType, Status, Visibility
from app.schemas.quest_editor import GraphEdge, GraphNode, SimulateIn, SimulateResult
from app.schemas.quest_validation import ValidationReport
from app.validation import run_validators


async def _audit(
    db: AsyncSession,
    *,
    actor_id: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
    request=None,
    reason: str | None = None,
) -> None:
    """Helper to log audit entries."""
    ip = None
    ua = None
    try:
        if request is not None and hasattr(request, "headers"):
            ip = request.headers.get("x-forwarded-for") or getattr(
                getattr(request, "client", None), "host", None
            )
            ua = request.headers.get("user-agent")
    except Exception:  # pragma: no cover - defensive
        pass
    service = AuditService(AuditLogRepository(db))
    await service.log(
        actor_id=actor_id or "",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before=before,
        after=after,
        ip=ip,
        user_agent=ua,
        reason=reason,
        extra=None,
    )


class NodeService:
    """Service layer for administrative node operations."""

    def __init__(
        self, db: AsyncSession, navcache: NavigationCacheService | None = None
    ) -> None:
        self._db = db
        self._navcache = navcache or NavigationCacheService(CoreCacheAdapter())
        self._allowed_types = {t.value for t in NodeType}

    # ------------------------------------------------------------------
    def _normalize_type(self, node_type: str | NodeType) -> str:
        value = node_type.value if isinstance(node_type, NodeType) else node_type
        if value not in self._allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported node type")
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
        if not item or item.workspace_id != workspace_id or item.type != node_type:
            raise HTTPException(status_code=404, detail="Node not found")
        await NodePatchDAO.overlay(self._db, [item])
        return item

    # Mutations ---------------------------------------------------------------
    async def create(
        self, workspace_id: UUID, node_type: str | NodeType, *, actor_id: UUID
    ) -> NodeItem:
        node_type = self._normalize_type(node_type)
        item = await NodeItemDAO.create(
            self._db,
            workspace_id=workspace_id,
            type=node_type,
            slug=f"{node_type}-{uuid4().hex[:8]}",
            title=f"New {node_type}",
            created_by_user_id=actor_id,
        )
        await self._db.commit()
        await _audit(
            self._db,
            actor_id=str(actor_id),
            action="node_create",
            resource_type=node_type,
            resource_id=str(item.id),
            after={"id": str(item.id)},
        )
        return item

    async def update(
        self,
        workspace_id: UUID,
        node_type: str | NodeType,
        node_id: UUID,
        data: dict[str, Any],
        *,
        actor_id: UUID,
        request=None,
    ) -> NodeItem:
        node_type = self._normalize_type(node_type)
        item = await self.get(workspace_id, node_type, node_id)
        before = {
            "title": item.title,
            "summary": item.summary,
            "status": item.status.value,
        }
        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        item.updated_by_user_id = actor_id
        item.updated_at = datetime.utcnow()
        await self._db.flush()
        await self._db.commit()
        try:
            await _audit(
                self._db,
                actor_id=str(actor_id),
                action="node_update",
                resource_type=node_type,
                resource_id=str(item.id),
                before=before,
                after={
                    "title": item.title,
                    "summary": item.summary,
                    "status": item.status.value,
                },
                request=request,
            )
        except Exception:
            pass
        return item

    async def publish(
        self,
        workspace_id: UUID,
        node_type: str | NodeType,
        node_id: UUID,
        *,
        actor_id: UUID,
        access: Literal["everyone", "premium_only", "early_access"] = "everyone",
        cover: str | None = None,
        request=None,
    ) -> NodeItem:
        node_type = self._normalize_type(node_type)
        item = await self.get(workspace_id, node_type, node_id)
        validate_transition(item.status, Status.published)
        if access == "early_access":
            item.visibility = Visibility.unlisted
        else:
            item.visibility = Visibility.public
        item.status = Status.published
        item.published_at = datetime.utcnow()
        item.updated_by_user_id = actor_id
        node = await self._db.get(Node, node_id)
        if node:
            node.premium_only = access == "premium_only"
            node.is_public = access != "early_access"
            node.visibility = (
                Visibility.unlisted if access == "early_access" else Visibility.public
            )
            if cover is not None:
                node.cover_url = cover
            node.updated_by_user_id = actor_id
            node.updated_at = datetime.utcnow()
        await self._db.flush()
        await self._db.commit()
        await publish_content(item.id, item.slug, actor_id)
        # Invalidate caches
        await self._navcache.invalidate_navigation_by_node(item.slug)
        await self._navcache.invalidate_modes_by_node(item.slug)
        await self._navcache.invalidate_compass_all()
        cache_invalidate("nav", reason="node_publish", key=item.slug)
        cache_invalidate("navm", reason="node_publish", key=item.slug)
        cache_invalidate("comp", reason="node_publish")
        # Traces (non-blocking, no-op chance)
        try:
            node_stub = Node(
                id=item.id,
                slug=item.slug,
                author_id=actor_id,
                workspace_id=item.workspace_id,
                content={},
            )
            user_stub = User(id=actor_id)
            await TracesService().maybe_add_auto_trace(
                self._db, node_stub, user_stub, chance=0.0
            )
        except Exception:  # pragma: no cover - tracing is best effort
            pass
        try:
            await _audit(
                self._db,
                actor_id=str(actor_id),
                action="node_publish",
                resource_type=node_type,
                resource_id=str(item.id),
                after={"status": Status.published.value},
                request=request,
            )
        except Exception:
            pass
        return item

    async def validate(
        self, node_type: str | NodeType, node_id: UUID
    ) -> Any:  # pragma: no cover - thin wrapper
        node_type = self._normalize_type(node_type)
        return await run_validators(node_type, node_id, self._db)

    async def simulate(
        self,
        workspace_id: UUID,
        node_type: str | NodeType,
        node_id: UUID,
        payload: SimulateIn,
    ) -> tuple[ValidationReport, SimulateResult]:
        node_type = self._normalize_type(node_type)
        if node_type != NodeType.quest.value:
            raise HTTPException(
                status_code=400, detail="Simulation supported only for quest nodes"
            )
        item = await self.get(workspace_id, node_type, node_id)
        data = item.quest_data or {}
        nodes = [GraphNode(**n) for n in data.get("nodes", [])]
        edges = [GraphEdge(**e) for e in data.get("edges", [])]
        report = await run_validators(node_type, node_id, self._db)
        result = EditorService().simulate_graph(nodes, edges, payload)
        return report, result

    async def apply_patch(
        self,
        node_id: UUID,
        data: dict[str, Any],
        *,
        actor_id: UUID | None = None,
    ):
        patch = await NodePatchDAO.create(
            self._db,
            node_id=node_id,
            data=data,
            created_by_user_id=actor_id,
        )
        await self._db.commit()
        return patch

    async def revert_patch(self, patch_id: UUID):
        patch = await NodePatchDAO.revert(self._db, patch_id=patch_id)
        await self._db.commit()
        if not patch:
            raise HTTPException(status_code=404, detail="Patch not found")
        return patch
