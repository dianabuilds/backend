from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.models.ai_system_v2 import AIModel
from app.domains.ai.infrastructure.repositories.system_v2_repository import (
    ModelsRepository,
    ProfilesRepository,
)
from app.domains.ai.validation_v2 import validate_routing_profile
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/ai/system",
    tags=["admin-ai-system"],
    responses=ADMIN_AUTH_RESPONSES,
)

AdminRequired = Annotated[None, Depends(require_admin_role())]


@router.get("/profiles")
async def list_profiles(
    _: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> list[dict[str, Any]]:
    repo = ProfilesRepository(db)
    rows = await repo.list()
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "enabled": bool(r.enabled),
            "rules": r.rules,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]


@router.post("/profiles")
async def create_profile(
    payload: dict[str, Any] = Body(...),
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    validate_routing_profile(payload)
    repo = ProfilesRepository(db)
    row = await repo.create(payload)
    return {"id": str(row.id), "name": row.name, "enabled": bool(row.enabled), "rules": row.rules}


@router.put("/profiles/{profile_id}")
async def update_profile(
    profile_id: str,
    payload: dict[str, Any] = Body(...),
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    validate_routing_profile(
        {
            **(payload or {}),
            "name": payload.get("name", "__tmp__"),
            "rules": payload.get("rules", []),
        }
    )
    repo = ProfilesRepository(db)
    row = await repo.update(profile_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="profile not found")
    return {"id": str(row.id), "name": row.name, "enabled": bool(row.enabled), "rules": row.rules}


@router.delete("/profiles/{profile_id}")
async def delete_profile(
    profile_id: str,
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = ProfilesRepository(db)
    await repo.delete(profile_id)
    return {"ok": True}


@router.post("/profiles/{profile_id}/validate")
async def validate_profile(
    profile_id: str,
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = ProfilesRepository(db)
    model_repo = ModelsRepository(db)
    prof = await repo.get(profile_id)
    if prof is None:
        raise HTTPException(status_code=404, detail="profile not found")
    errors: list[str] = []
    # Load models into a map for quick checks
    models = {str(m.id): m for m in await model_repo.list()}
    for idx, rule in enumerate(prof.rules or []):
        route = (rule or {}).get("route") or {}
        model_id = route.get("model_id")
        m: AIModel | None = models.get(model_id)
        if m is None:
            errors.append(f"rule[{idx}]: model not found: {model_id}")
            continue
        caps_req = set((rule.get("selector") or {}).get("capabilities") or [])
        caps_have = set(m.capabilities or [])
        if not caps_req.issubset(caps_have):
            errors.append(f"rule[{idx}]: missing capabilities: {sorted(caps_req - caps_have)}")
        # min_context vs limits
        min_ctx = (rule.get("selector") or {}).get("min_context")
        if isinstance(min_ctx, int):
            max_in = (m.limits or {}).get("max_input_tokens")
            if isinstance(max_in, int) and max_in < min_ctx:
                errors.append(f"rule[{idx}]: min_context {min_ctx} exceeds model limit {max_in}")
        # price check
        max_price = (rule.get("selector") or {}).get("max_price_per_1k")
        if isinstance(max_price, int | float):
            price = (m.pricing or {}).get("input_per_1k")
            if isinstance(price, int | float) and price > max_price:
                errors.append(f"rule[{idx}]: input price {price} exceeds {max_price}")
    return {"ok": len(errors) == 0, "errors": errors}
