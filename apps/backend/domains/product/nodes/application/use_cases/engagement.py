from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException

from domains.product.nodes.application.use_cases.helpers import resolve_node_ref
from domains.product.nodes.application.use_cases.ports import NodesServicePort
from domains.product.nodes.infrastructure.engine import ensure_engine
from domains.product.nodes.infrastructure.saved_views_repository import (
    SavedViewRecord,
    SavedViewsRepository,
    SavedViewsUnavailable,
)
from domains.product.nodes.utils import (
    normalize_actor_id,
    parse_request_datetime,
    reactions_summary_to_dict,
    view_stat_to_dict,
)


@dataclass
class EngagementService:
    nodes_service: NodesServicePort
    saved_views: SavedViewsRepository | None = None

    async def register_view(
        self,
        node_ref: str,
        payload: Mapping[str, Any] | None,
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        view, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        body = payload or {}
        amount = body.get("amount", 1)
        try:
            amount_value = int(amount)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="amount_invalid") from None
        fingerprint = body.get("fingerprint")
        if fingerprint is not None and not isinstance(fingerprint, str):
            raise HTTPException(status_code=400, detail="fingerprint_invalid")
        at_raw = body.get("at")
        at_dt = None
        if at_raw is not None:
            if not isinstance(at_raw, str):
                raise HTTPException(status_code=400, detail="timestamp_invalid")
            try:
                at_dt = parse_request_datetime(at_raw)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        actor_id = normalize_actor_id(claims)
        total = await self.nodes_service.register_view(
            node_id,
            viewer_id=actor_id or None,
            fingerprint=fingerprint,
            amount=amount_value,
            at=at_dt,
        )
        return {"id": node_id, "views_count": total}

    async def get_views(
        self,
        node_ref: str,
        *,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        if limit < 1 or limit > 90:
            raise HTTPException(status_code=400, detail="limit_invalid")
        if offset < 0:
            raise HTTPException(status_code=400, detail="offset_invalid")
        _, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        total = await self.nodes_service.get_total_views(node_id)
        stats = await self.nodes_service.get_view_stats(
            node_id, limit=limit, offset=offset
        )
        return {
            "id": node_id,
            "total": total,
            "buckets": [view_stat_to_dict(stat) for stat in stats],
        }

    async def add_like(
        self,
        node_ref: str,
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        _, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        actor_id = self._require_actor(claims)
        liked = await self.nodes_service.add_like(node_id, user_id=actor_id)
        summary = await self.nodes_service.get_reactions_summary(
            node_id, user_id=actor_id
        )
        return {
            "id": node_id,
            "liked": liked,
            "summary": reactions_summary_to_dict(summary),
        }

    async def remove_like(
        self,
        node_ref: str,
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        _, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        actor_id = self._require_actor(claims)
        removed = await self.nodes_service.remove_like(node_id, user_id=actor_id)
        summary = await self.nodes_service.get_reactions_summary(
            node_id, user_id=actor_id
        )
        return {
            "id": node_id,
            "liked": not removed,
            "summary": reactions_summary_to_dict(summary),
        }

    async def get_reactions(
        self,
        node_ref: str,
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        _, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        actor_id = normalize_actor_id(claims)
        summary = await self.nodes_service.get_reactions_summary(
            node_id, user_id=actor_id or None
        )
        return reactions_summary_to_dict(summary)

    async def list_saved_views(
        self,
        claims: Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        repo = self._require_saved_views()
        actor_id = self._require_actor(claims)
        rows = await repo.list_for_user(actor_id)
        return [self._present_saved_view(row) for row in rows]

    async def upsert_saved_view(
        self,
        body: Mapping[str, Any],
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        repo = self._require_saved_views()
        actor_id = self._require_actor(claims)
        name = body.get("name")
        if not isinstance(name, str) or not name.strip():
            raise HTTPException(status_code=400, detail="name_required")
        config = body.get("config")
        if config is None:
            raise HTTPException(status_code=400, detail="config_required")
        if not isinstance(config, dict):
            raise HTTPException(status_code=400, detail="config_invalid")
        self._validate_saved_view_config(config)
        is_default = bool(body.get("is_default", False))
        try:
            await repo.upsert(
                actor_id,
                name=name.strip(),
                config=config,
                is_default=is_default,
            )
        except SavedViewsUnavailable as exc:
            raise HTTPException(status_code=503, detail="no_engine") from exc
        return {"ok": True}

    async def delete_saved_view(
        self,
        name: str,
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        repo = self._require_saved_views()
        actor_id = self._require_actor(claims)
        try:
            await repo.delete(actor_id, name)
        except SavedViewsUnavailable as exc:
            raise HTTPException(status_code=503, detail="no_engine") from exc
        return {"ok": True}

    async def set_default_saved_view(
        self,
        name: str,
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        repo = self._require_saved_views()
        actor_id = self._require_actor(claims)
        try:
            await repo.set_default(actor_id, name)
        except SavedViewsUnavailable as exc:
            raise HTTPException(status_code=503, detail="no_engine") from exc
        return {"ok": True}

    def _require_actor(self, claims: Mapping[str, Any] | None) -> str:
        actor_id = normalize_actor_id(claims)
        if not actor_id:
            raise HTTPException(status_code=401, detail="unauthorized")
        return actor_id

    def _require_saved_views(self) -> SavedViewsRepository:
        if self.saved_views is None:
            raise HTTPException(status_code=503, detail="no_engine")
        return self.saved_views

    def _validate_saved_view_config(self, config: Mapping[str, Any]) -> None:
        filters = config.get("filters")
        if filters is not None and not isinstance(filters, Mapping):
            raise HTTPException(status_code=400, detail="filters_invalid")
        if isinstance(filters, Mapping):
            if (
                "q" in filters
                and filters["q"] is not None
                and not isinstance(filters["q"], str)
            ):
                raise HTTPException(status_code=400, detail="filters_q_invalid")
            if (
                "slug" in filters
                and filters["slug"] is not None
                and not isinstance(filters["slug"], str)
            ):
                raise HTTPException(status_code=400, detail="filters_slug_invalid")
            if filters.get("status") is not None:
                status = str(filters["status"]).lower()
                allowed = {
                    "all",
                    "draft",
                    "published",
                    "scheduled",
                    "scheduled_unpublish",
                    "archived",
                    "deleted",
                }
                if status not in allowed:
                    raise HTTPException(
                        status_code=400, detail="filters_status_invalid"
                    )
        page_size = config.get("pageSize")
        if page_size is not None:
            try:
                size = int(page_size)
                if size < 5 or size > 200:
                    raise ValueError
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=400, detail="pageSize_invalid"
                ) from None
        sort = config.get("sort")
        if sort is not None:
            allowed_sort = {"updated_at", "title", "author", "status"}
            if str(sort).lower() not in allowed_sort:
                raise HTTPException(status_code=400, detail="sort_invalid")
        order = config.get("order")
        if order is not None:
            if str(order).lower() not in {"asc", "desc"}:
                raise HTTPException(status_code=400, detail="order_invalid")
        columns = config.get("columns")
        if columns is not None and not isinstance(columns, Mapping):
            raise HTTPException(status_code=400, detail="columns_invalid")

    def _present_saved_view(self, record: SavedViewRecord) -> dict[str, Any]:
        return {
            "name": record.name,
            "config": record.config,
            "is_default": bool(record.is_default),
            "updated_at": record.updated_at,
        }


def build_engagement_service(container: Any) -> EngagementService:
    saved_repo: SavedViewsRepository | None = None
    try:
        saved_repo = SavedViewsRepository(lambda: ensure_engine(container))
    except Exception:  # pragma: no cover - defensive
        saved_repo = None
    return EngagementService(
        nodes_service=container.nodes_service,
        saved_views=saved_repo,
    )
