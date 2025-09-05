from __future__ import annotations

import csv
import io
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounts.infrastructure.dao import AccountDAO
from app.domains.ai.infrastructure.repositories.usage_repository import (
    AIUsageRepository,
)
from app.providers.db.session import get_db
from app.schemas.accounts import AccountSettings
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/ai/usage",
    tags=["admin-ai-usage"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("/system", summary="System-wide usage totals")
async def get_system_usage(
    _: Annotated[object, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict:
    repo = AIUsageRepository(db)
    return await repo.system_totals()


@router.get("/accounts", summary="Usage by account", response_model=None)
async def get_usage_by_account(
    format: Annotated[str | None, Query()] = None,
    _: Annotated[object, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    repo = AIUsageRepository(db)
    rows = await repo.by_account()
    # attach limits for progress bar
    out: list[dict] = []
    for r in rows:
        acc = await AccountDAO.get(db, r["account_id"])
        limit = 0
        if acc:
            settings = AccountSettings.model_validate(acc.settings_json)
            limit = int(settings.limits.get("ai_tokens", 0))
        progress = r["tokens"] / limit if limit else 0
        out.append({**r, "limit": limit, "progress": progress})
    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["account_id", "tokens", "cost", "limit", "progress"])
        for r in out:
            writer.writerow([r["account_id"], r["tokens"], r["cost"], r["limit"], r["progress"]])
        return Response(buf.getvalue(), media_type="text/csv")
    return out


@router.get(
    "/accounts/{account_id}/users",
    summary="Usage by user in account",
    response_model=None,
)
async def get_usage_by_user(
    account_id: Annotated[int, Path()],
    format: Annotated[str | None, Query()] = None,
    _: Annotated[object, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    repo = AIUsageRepository(db)
    rows = await repo.by_user(account_id)
    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["user_id", "tokens", "cost"])
        for r in rows:
            writer.writerow([r["user_id"], r["tokens"], r["cost"]])
        return Response(buf.getvalue(), media_type="text/csv")
    return rows


@router.get(
    "/accounts/{account_id}/models",
    summary="Usage by model in account",
    response_model=None,
)
async def get_usage_by_model(
    account_id: Annotated[int, Path()],
    format: Annotated[str | None, Query()] = None,
    _: Annotated[object, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    repo = AIUsageRepository(db)
    rows = await repo.by_model(account_id)
    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["model", "tokens", "cost"])
        for r in rows:
            writer.writerow([r["model"], r["tokens"], r["cost"]])
        return Response(buf.getvalue(), media_type="text/csv")
    return rows
