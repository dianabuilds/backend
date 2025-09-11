from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.repositories.system_v2_repository import (
    ModelsRepository,
    ProvidersRepository,
)
from app.domains.ai.validation_v2 import validate_manifest, validate_secrets
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/ai/system",
    tags=["admin-ai-system"],
    responses=ADMIN_AUTH_RESPONSES,
)

AdminRequired = Annotated[None, Depends(require_admin_role())]


@router.get("/providers")
async def list_providers(
    _: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> list[dict[str, Any]]:
    repo = ProvidersRepository(db)
    rows = await repo.list()
    return [
        {
            "id": str(r.id),
            "code": r.code,
            "name": r.name,
            "base_url": r.base_url,
            "health": r.health,
        }
        for r in rows
    ]


@router.post("/providers")
async def create_provider(
    payload: dict[str, Any] = Body(...),
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = ProvidersRepository(db)
    row = await repo.create(payload)
    return {
        "id": str(row.id),
        "code": row.code,
        "name": row.name,
        "base_url": row.base_url,
        "health": row.health,
    }


@router.put("/providers/{provider_id}")
async def update_provider(
    provider_id: str,
    payload: dict[str, Any] = Body(...),
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = ProvidersRepository(db)
    row = await repo.update(provider_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="provider not found")
    return {
        "id": str(row.id),
        "code": row.code,
        "name": row.name,
        "base_url": row.base_url,
        "health": row.health,
    }


@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = ProvidersRepository(db)
    await repo.delete(provider_id)
    return {"ok": True}


@router.get("/providers/{provider_id}/manifest")
async def get_manifest(
    provider_id: str,
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any] | None:
    repo = ProvidersRepository(db)
    row = await repo.get(provider_id)
    if row is None:
        raise HTTPException(status_code=404, detail="provider not found")
    return row.manifest


@router.put("/providers/{provider_id}/manifest")
async def put_manifest(
    provider_id: str,
    manifest: dict[str, Any] = Body(...),
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    validate_manifest(manifest)
    providers = ProvidersRepository(db)
    models_repo = ModelsRepository(db)
    row = await providers.update(provider_id, {"manifest": manifest})
    if row is None:
        raise HTTPException(status_code=404, detail="provider not found")
    # upsert models from manifest
    for model in manifest.get("models", []) or []:
        await models_repo.upsert_from_manifest(provider_id, model)
    return {"ok": True}


@router.post("/providers/{provider_id}/secrets")
async def set_secrets(
    provider_id: str,
    secrets: dict[str, Any] = Body(...),
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    validate_secrets(secrets)
    repo = ProvidersRepository(db)
    await repo.set_secrets(provider_id, {k: str(v) for k, v in secrets.items()})
    return {"ok": True}


@router.post("/providers/{provider_id}/refresh_prices")
async def refresh_prices(
    provider_id: str,
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    # Placeholder: in future enqueue a background job
    repo = ProvidersRepository(db)
    row = await repo.get(provider_id)
    if row is None:
        raise HTTPException(status_code=404, detail="provider not found")
    return {"status": "queued"}
