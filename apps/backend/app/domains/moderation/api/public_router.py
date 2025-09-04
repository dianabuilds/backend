from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.rate_limit import rate_limit_dep
from app.domains.moderation.application import CasesService
from app.domains.users.infrastructure.models.user import User
from app.schemas.moderation_cases import CaseCreate

cases_service = CasesService()

router = APIRouter(
    prefix="/moderation/cases",
    tags=["moderation"],
    dependencies=[rate_limit_dep("5/min")],
)


@router.post("", response_model=dict[str, UUID])
async def create_case(
    body: CaseCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, UUID]:
    data = body.model_copy(update={"reporter_id": current_user.id})
    case_id = await cases_service.create_case(db, data)
    return {"id": case_id}
