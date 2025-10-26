from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from domains.product.navigation.application.ports import TransitionRequest
from domains.product.navigation.domain.transition import (
    TransitionCandidate,
)
from domains.product.nodes.application.admin_queries.use_cases import (
    DEV_BLOG_TAG,
    list_nodes_admin,
)

logger = logging.getLogger(__name__)

DEFAULT_PREVIEW_LIMIT = 6
MAX_PREVIEW_LIMIT = 12

NODE_TAGS: dict[str, str] = {
    "quests_carousel": "quest",
}


async def get_block_preview(
    container: Any,
    block: str,
    *,
    locale: str = "ru",
    limit: int = DEFAULT_PREVIEW_LIMIT,
) -> dict[str, Any]:
    block_id = (block or "").strip().lower()
    locale = (locale or "ru").strip() or "ru"
    effective_limit = max(1, min(limit, MAX_PREVIEW_LIMIT))
    fetched_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    meta: dict[str, Any] = {"block": block_id}

    if not block_id:
        return _empty_preview(block_id, locale, fetched_at, meta, source="invalid")

    try:
        if block_id == "recommendations":
            items, source, meta_update = await _preview_recommendations(container, effective_limit)
            meta.update(meta_update)
            if items:
                return _build_preview(block_id, locale, fetched_at, source, items, meta)
            meta.setdefault("reason", "recommendations_empty")
            return _fallback_preview(block_id, locale, fetched_at, meta)

        if block_id == "dev_blog_list":
            items = await _preview_nodes(
                container,
                tag=DEV_BLOG_TAG,
                sort="updated_at",
                order="desc",
                limit=effective_limit,
            )
            if items:
                return _build_preview(block_id, locale, fetched_at, "live", items, meta)
            meta.setdefault("reason", "dev_blog_empty")
            return _fallback_preview(block_id, locale, fetched_at, meta)

        if block_id in ("nodes_carousel", "quests_carousel", "popular_carousel"):
            tag = NODE_TAGS.get(block_id)
            sort = "updated_at"
            order = "desc"
            if block_id == "popular_carousel":
                sort = "views"
            items = await _preview_nodes(
                container,
                tag=tag,
                sort=sort,
                order=order,
                limit=effective_limit,
            )
            if items:
                return _build_preview(block_id, locale, fetched_at, "live", items, meta)
            meta.setdefault("reason", "nodes_empty")
            return _fallback_preview(block_id, locale, fetched_at, meta)

        meta.setdefault("reason", "preview_not_configured")
        return _fallback_preview(block_id, locale, fetched_at, meta)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning(
            "site.preview_block_failed",
            extra={"block": block_id, "locale": locale, "error": str(exc)},
            exc_info=exc,
        )
        meta.setdefault("reason", "preview_exception")
        return _fallback_preview(block_id, locale, fetched_at, meta)


async def _preview_nodes(
    container: Any,
    *,
    tag: str | None,
    sort: str,
    order: str,
    limit: int,
) -> list[dict[str, Any]]:
    nodes = await list_nodes_admin(
        container,
        q=None,
        slug=None,
        tag=tag,
        author_id=None,
        limit=limit,
        offset=0,
        status="published",
        moderation_status=None,
        updated_from=None,
        updated_to=None,
        sort=sort,
        order=order,
    )
    return [_node_to_preview(node) for node in nodes if node.get("title")]


async def _preview_recommendations(
    container: Any,
    limit: int,
) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    navigation = getattr(container, "navigation_service", None)
    nodes_service = getattr(container, "nodes_service", None)
    meta: dict[str, Any] = {}
    items: list[dict[str, Any]]

    if navigation is None or nodes_service is None:
        meta["reason"] = "navigation_unavailable"
        items = await _preview_nodes(
            container,
            tag=None,
            sort="views",
            order="desc",
            limit=limit,
        )
        return items, ("live" if items else "fallback"), meta

    request = TransitionRequest(
        user_id="site-preview",
        session_id=f"site-preview-{uuid4()}",
        origin_node_id=None,
        route_window=(),
        limit_state="normal",
        mode="site_preview",
        requested_ui_slots=limit,
        premium_level="free",
        policies_hash=None,
        requested_provider_overrides=None,
        emergency=False,
    )

    try:
        decision = await asyncio.to_thread(navigation.next, request)
    except Exception as exc:  # pragma: no cover - depends on navigation impl
        meta["reason"] = "navigation_error"
        logger.warning(
            "site.preview.navigation_error",
            extra={"error": str(exc)},
            exc_info=exc,
        )
        return [], "error", meta

    meta.update(
        {
            "mode": decision.mode,
            "pool_size": decision.pool_size,
            "limit_state": decision.limit_state,
            "served_from_cache": decision.served_from_cache,
        }
    )

    candidates = list(decision.candidates[:limit])
    if not candidates:
        meta.setdefault("reason", "no_candidates")
        return [], "live", meta

    items = []
    for candidate in candidates:
        dto = await nodes_service._repo_get_async(candidate.node_id)  # type: ignore[attr-defined]
        if dto is None:
            continue
        slug = getattr(dto, "slug", None)
        title = getattr(dto, "title", None) or slug or f"Node #{candidate.node_id}"
        items.append(
            {
                "id": str(candidate.node_id),
                "title": title,
                "subtitle": _build_candidate_subtitle(candidate),
                "href": f"/n/{slug}" if slug else None,
                "badge": candidate.badge,
                "provider": candidate.provider,
                "score": candidate.score,
                "probability": candidate.probability,
            }
        )

    source = "live" if items else "live_empty"
    if not items:
        meta.setdefault("reason", "candidate_details_missing")
    return items, source, meta


def _build_candidate_subtitle(candidate: TransitionCandidate) -> str | None:
    explain = candidate.explain.strip()
    if explain:
        return explain
    factors = candidate.factors or {}
    parts: list[str] = []
    if candidate.badge:
        parts.append(candidate.badge)
    if "similarity" in factors:
        parts.append(f"similarity {factors['similarity']:.2f}")
    if "tag_overlap" in factors:
        parts.append(f"overlap {factors['tag_overlap']:.2f}")
    if "author_match" in factors:
        parts.append(f"author {factors['author_match']:.0f}")
    if candidate.probability > 0:
        parts.append(f"p={candidate.probability:.2f}")
    return " · ".join(parts) if parts else None


def _node_to_preview(node: dict[str, Any]) -> dict[str, Any]:
    slug = node.get("slug")
    title = node.get("title") or slug or f"Node #{node.get('id')}"
    subtitle_parts: list[str] = []
    if node.get("author_name"):
        subtitle_parts.append(str(node["author_name"]))
    updated = node.get("updated_at")
    if isinstance(updated, str):
        subtitle_parts.append(updated[:10])
    return {
        "id": str(node.get("id")),
        "title": title,
        "subtitle": " · ".join(subtitle_parts) if subtitle_parts else None,
        "href": f"/n/{slug}" if slug else None,
        "badge": None,
    }


def _fallback_preview(
    block: str,
    locale: str,
    fetched_at: str,
    meta: dict[str, Any],
) -> dict[str, Any]:
    return _build_preview(block, locale, fetched_at, "mock", [], meta)


def _empty_preview(
    block: str,
    locale: str,
    fetched_at: str,
    meta: dict[str, Any],
    *,
    source: str,
) -> dict[str, Any]:
    return _build_preview(block, locale, fetched_at, source, [], meta)


def _build_preview(
    block: str,
    locale: str,
    fetched_at: str,
    source: str,
    items: Iterable[dict[str, Any]],
    meta: dict[str, Any],
) -> dict[str, Any]:
    return {
        "block": block,
        "locale": locale,
        "fetched_at": fetched_at,
        "source": source,
        "items": list(items),
        "meta": meta,
    }


__all__ = ["get_block_preview"]
