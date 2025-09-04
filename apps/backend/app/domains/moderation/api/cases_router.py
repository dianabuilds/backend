from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.moderation.application import CasesService
from app.providers.case_notifier import ICaseNotifier
from app.schemas.moderation_cases import (
    CaseClose,
    CaseCreate,
    CaseFullResponse,
    CaseLabelsPatch,
    CaseListResponse,
    CaseNoteCreate,
    CaseNoteOut,
    CaseOut,
    CasePatch,
)
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

cases_service = CasesService()
admin_required = require_admin_role()


def get_notifier(request: Request) -> ICaseNotifier | None:
    container = getattr(request.app.state, "container", None)
    if container:
        try:
            return container.resolve(ICaseNotifier)
        except Exception:
            return None
    return None


router = APIRouter(
    prefix="/admin/moderation/cases",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("", response_model=CaseListResponse)
async def list_cases(
    page: int = 1,
    size: int = 20,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> CaseListResponse:
    return await cases_service.list_cases(db, page=page, size=size)


@router.post("", response_model=dict[str, UUID])
async def create_case(
    body: CaseCreate,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
    notifier: Annotated[ICaseNotifier | None, Depends(get_notifier)] = None,
) -> dict[str, UUID]:
    case_id = await cases_service.create_case(db, body, notifier)
    return {"id": case_id}


@router.get("/{case_id}", response_model=CaseFullResponse)
async def get_case(
    case_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> CaseFullResponse:
    result = await cases_service.get_case(db, case_id)
    if not result:
        raise HTTPException(status_code=404, detail="Case not found")
    return result


@router.patch("/{case_id}", response_model=CaseOut)
async def patch_case(
    case_id: UUID,
    patch: CasePatch,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> CaseOut:
    case = await cases_service.patch_case(db, case_id, patch)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}/labels", response_model=CaseOut)
async def patch_labels(
    case_id: UUID,
    patch: CaseLabelsPatch,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> CaseOut:
    case = await cases_service.patch_labels(db, case_id, patch)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.post("/{case_id}/notes", response_model=CaseNoteOut)
async def add_note(
    case_id: UUID,
    note: CaseNoteCreate,
    current: Annotated[Any, Depends(admin_required)],
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> CaseNoteOut:
    res = await cases_service.add_note(db, case_id, note, getattr(current, "id", None))
    if not res:
        raise HTTPException(status_code=404, detail="Case not found")
    return res


@router.post("/{case_id}/actions/close")
async def close_case(
    case_id: UUID,
    payload: CaseClose,
    current: Annotated[Any, Depends(admin_required)],
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, str]:
    res = await cases_service.close_case(
        db, case_id, payload, getattr(current, "id", None)
    )
    if not res:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"status": "ok"}
