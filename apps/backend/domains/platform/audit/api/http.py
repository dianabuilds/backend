from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from io import StringIO
from typing import Any

from app.api_gateway.routers import get_container
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from domains.platform.iam.security import csrf_protect, require_admin

# from app.api_gateway.routers import get_container
from packages.fastapi_rate_limit import optional_rate_limiter


def _parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [chunk.strip() for chunk in value.split(",") if chunk.strip()]


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("created_at") is None:
        ts = row.get("ts")
        if isinstance(ts, (int, float)):
            row["created_at"] = datetime.fromtimestamp(
                float(ts) / 1000.0, tz=UTC
            ).isoformat()
    elif isinstance(row.get("created_at"), datetime):
        row["created_at"] = row["created_at"].astimezone(UTC).isoformat()
    return row


def _safe_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        import json

        return json.loads(value)
    except (ValueError, TypeError):
        return value


def _split_action(action: str) -> tuple[str, str]:
    if not action:
        return "unknown", "unknown"
    parts = action.split(".")
    if len(parts) == 1:
        return parts[0], parts[0]
    return parts[0], ".".join(parts[1:])


def _infer_result(action: str, extra: Any) -> str:
    lowered = action.lower()
    failure_markers = ["fail", "failed", "error", "denied", "rejected"]
    if any(marker in lowered for marker in failure_markers):
        return "failure"
    if isinstance(extra, dict):
        err = extra.get("error") or extra.get("status")
        if (
            err
            and isinstance(err, str)
            and err.lower() in {"error", "failed", "denied"}
        ):
            return "failure"
    return "success"


def _resource_label(row: dict[str, Any]) -> str:
    rtype = row.get("resource_type") or "resource"
    rid = row.get("resource_id") or ""
    if rid:
        return f"{rtype}:{rid}"
    return str(rtype)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/audit", tags=["audit"])

    @router.get("")
    async def list_events(
        req: Request,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=200),
        actions: list[str] | None = Query(default=None),
        action: str | None = Query(default=None),
        actor_id: str | None = Query(default=None),
        actor: str | None = Query(default=None),
        date_from: str | None = Query(default=None, alias="from"),
        date_to: str | None = Query(default=None, alias="to"),
        resource_type: str | None = Query(default=None),
        resource_types: list[str] | None = Query(default=None),
        module: str | None = Query(default=None),
        modules: list[str] | None = Query(default=None),
        result: str | None = Query(default=None, pattern="^(success|failure)$"),
        search: str | None = Query(default=None, alias="q"),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        container = get_container(req)
        repo = container.audit.repo

        acts = list(actions or [])
        if action:
            acts.extend(_parse_csv(action))
        res_types = list(resource_types or [])
        res_types.extend(_parse_csv(resource_type))
        mods = list(modules or [])
        mods.extend(_parse_csv(module))
        per_page = int(page_size)
        offset = (int(page) - 1) * per_page

        raw_items = await repo.list(
            limit=per_page + 1,
            offset=offset,
            actions=acts or None,
            actor_id=actor or actor_id,
            date_from=date_from,
            date_to=date_to,
            resource_types=res_types or None,
            modules=mods or None,
            search=search,
        )

        processed: list[dict[str, Any]] = []
        for row in raw_items[:per_page]:
            normalized = _normalize_row(dict(row))
            extra_obj = _safe_json(normalized.get("extra"))
            before_obj = _safe_json(normalized.get("before"))
            after_obj = _safe_json(normalized.get("after"))
            module_name, verb = _split_action(str(normalized.get("action", "")))
            outcome = _infer_result(str(normalized.get("action", "")), extra_obj)
            item = {
                "id": str(normalized.get("id")),
                "created_at": normalized.get("created_at"),
                "actor_id": normalized.get("actor_id"),
                "action": normalized.get("action"),
                "resource_type": normalized.get("resource_type"),
                "resource_id": normalized.get("resource_id"),
                "reason": normalized.get("reason"),
                "ip": normalized.get("ip"),
                "user_agent": normalized.get("user_agent"),
                "before": before_obj,
                "after": after_obj,
                "extra": extra_obj,
                "meta": {
                    "module": module_name,
                    "verb": verb,
                    "resource_label": _resource_label(normalized),
                    "result": outcome,
                },
            }
            processed.append(item)

        if result in {"success", "failure"}:
            processed = [item for item in processed if item["meta"]["result"] == result]

        has_more = len(raw_items) > per_page
        facets = {
            "modules": Counter(item["meta"]["module"] for item in processed),
            "resource_types": Counter(
                (item.get("resource_type") or "unknown") for item in processed
            ),
            "results": Counter(item["meta"]["result"] for item in processed),
        }
        taxonomy_actions = sorted(
            {item["action"] for item in processed if item.get("action")}
        )

        return {
            "items": processed,
            "page": page,
            "page_size": per_page,
            "has_more": has_more,
            "next_page": page + 1 if has_more else None,
            "facets": {
                key: {k: v for k, v in counter.items() if v}
                for key, counter in facets.items()
            },
            "taxonomy": {
                "actions": taxonomy_actions,
            },
        }

    @router.get("/export")
    async def export_events(
        req: Request,
        export_format: str = Query(
            default="json", pattern="^(json|csv)$", alias="format"
        ),
        limit: int = Query(default=5000, ge=1, le=20000),
        actions: list[str] | None = Query(default=None),
        action: str | None = Query(default=None),
        actor_id: str | None = Query(default=None),
        actor: str | None = Query(default=None),
        date_from: str | None = Query(default=None, alias="from"),
        date_to: str | None = Query(default=None, alias="to"),
        resource_type: str | None = Query(default=None),
        module: str | None = Query(default=None),
        search: str | None = Query(default=None, alias="q"),
        _admin: None = Depends(require_admin),
    ) -> Any:
        container = get_container(req)
        repo = container.audit.repo
        action_filters = list(actions or [])
        if action:
            action_filters.extend(_parse_csv(action))
        resource_filters = _parse_csv(resource_type)
        module_filters = _parse_csv(module)
        items = await repo.list(
            limit=int(limit),
            offset=0,
            actions=action_filters or None,
            actor_id=actor or actor_id,
            date_from=date_from,
            date_to=date_to,
            resource_types=resource_filters or None,
            modules=module_filters or None,
            search=search,
        )
        processed = []
        for row in items:
            normalized = _normalize_row(dict(row))
            extra_obj = _safe_json(normalized.get("extra"))
            before_obj = _safe_json(normalized.get("before"))
            after_obj = _safe_json(normalized.get("after"))
            module_name, verb = _split_action(str(normalized.get("action", "")))
            processed.append(
                {
                    "id": str(normalized.get("id")),
                    "created_at": normalized.get("created_at"),
                    "actor_id": normalized.get("actor_id"),
                    "action": normalized.get("action"),
                    "module": module_name,
                    "verb": verb,
                    "resource_type": normalized.get("resource_type"),
                    "resource_id": normalized.get("resource_id"),
                    "reason": normalized.get("reason"),
                    "ip": normalized.get("ip"),
                    "user_agent": normalized.get("user_agent"),
                    "before": before_obj,
                    "after": after_obj,
                    "extra": extra_obj,
                    "result": _infer_result(
                        str(normalized.get("action", "")), extra_obj
                    ),
                }
            )
        if export_format == "json":
            return JSONResponse(content={"items": processed})
        columns = [
            "id",
            "created_at",
            "actor_id",
            "action",
            "module",
            "verb",
            "resource_type",
            "resource_id",
            "result",
            "reason",
            "ip",
            "user_agent",
        ]
        csv_buffer = StringIO()
        import csv

        writer = csv.DictWriter(csv_buffer, fieldnames=columns)
        writer.writeheader()
        for row in processed:
            flat = {key: row.get(key) for key in columns}
            writer.writerow(flat)
        response = PlainTextResponse(csv_buffer.getvalue())
        response.headers["Content-Disposition"] = (
            "attachment; filename=audit-export.csv"
        )
        return response

    @router.post("")
    @router.post(
        "",
        dependencies=(optional_rate_limiter(times=20, seconds=60)),
    )
    async def log_event(
        req: Request,
        payload: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        container = get_container(req)
        p = payload or {}
        await container.audit.service.log(
            actor_id=p.get("actor_id"),
            action=str(p.get("action", "")),
            resource_type=p.get("resource_type"),
            resource_id=p.get("resource_id"),
            before=p.get("before"),
            after=p.get("after"),
            ip=p.get("ip"),
            user_agent=p.get("user_agent"),
            reason=p.get("reason"),
            extra=p.get("extra"),
        )
        return {"ok": True}

    return router
