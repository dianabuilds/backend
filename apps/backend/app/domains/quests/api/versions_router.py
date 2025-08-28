# ruff: noqa: B008
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    assert_owner_or_role,
    get_current_user,
    get_db,
    get_preview_context,
)
from app.core.preview import PreviewContext
from app.domains.quests.application.editor_service import EditorService
from app.domains.quests.application.quest_graph_service import QuestGraphService
from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.quests.infrastructure.models.quest_version_models import QuestVersion
from app.domains.quests.schemas import (
    QuestGraphIn,
    QuestGraphOut,
    QuestVersionOut,
)
from app.domains.users.infrastructure.models.user import User
from app.schemas.quest_editor import SimulateIn, SimulateResult, ValidateResult

router = APIRouter(prefix="/quests", tags=["quests"])


async def _ensure_quest_access(
    db: AsyncSession, quest_id: UUID, workspace_id: UUID, current_user: User
) -> Quest:
    quest = await db.get(Quest, quest_id)
    if not quest or quest.workspace_id != workspace_id or quest.is_deleted:
        raise HTTPException(status_code=404, detail="Quest not found")
    assert_owner_or_role(quest.author_id, "moderator", current_user)
    return quest


async def _ensure_version_access(
    db: AsyncSession, version_id: UUID, workspace_id: UUID, current_user: User
) -> QuestVersion:
    version = await db.get(QuestVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    await _ensure_quest_access(db, version.quest_id, workspace_id, current_user)
    return version


@router.get(
    "/{quest_id}/versions",
    response_model=list[QuestVersionOut],
    summary="List quest versions",
)
async def list_versions(
    quest_id: UUID,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_quest_access(db, quest_id, workspace_id, current_user)
    res = await db.execute(
        select(QuestVersion)
        .where(QuestVersion.quest_id == quest_id)
        .order_by(QuestVersion.number)
    )
    versions = res.scalars().all()
    return [QuestVersionOut.model_validate(v, from_attributes=True) for v in versions]


@router.post(
    "/{quest_id}/versions",
    response_model=QuestVersionOut,
    summary="Create quest version",
)
async def create_version(
    quest_id: UUID,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_quest_access(db, quest_id, workspace_id, current_user)
    svc = EditorService()
    version = await svc.create_version(db, quest_id, actor_id=current_user.id)
    await db.commit()
    await db.refresh(version)
    return QuestVersionOut.model_validate(version, from_attributes=True)


@router.get(
    "/{quest_id}/versions/current",
    response_model=QuestGraphOut,
    summary="Get current quest version graph",
)
async def get_current_version(
    quest_id: UUID,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_quest_access(db, quest_id, workspace_id, current_user)
    res = await db.execute(
        select(QuestVersion)
        .where(
            QuestVersion.quest_id == quest_id,
            QuestVersion.status == "released",
        )
        .order_by(QuestVersion.number.desc())
        .limit(1)
    )
    version = res.scalars().first()
    if not version:
        raise HTTPException(status_code=404, detail="Released version not found")
    svc = QuestGraphService()
    v, steps, transitions = await svc.load_graph(db, version.id)
    return QuestGraphOut(
        version=QuestVersionOut.model_validate(v, from_attributes=True),
        steps=steps,
        transitions=transitions,
    )


@router.get(
    "/{quest_id}/versions/{version_id}",
    response_model=QuestVersionOut,
    summary="Get quest version",
)
async def get_version(
    quest_id: UUID,
    version_id: UUID,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await _ensure_version_access(db, version_id, workspace_id, current_user)
    if version.quest_id != quest_id:
        raise HTTPException(status_code=404, detail="Version not found")
    return QuestVersionOut.model_validate(version, from_attributes=True)


@router.delete("/{quest_id}/versions/{version_id}", summary="Delete draft version")
async def delete_version(
    quest_id: UUID,
    version_id: UUID,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await _ensure_version_access(db, version_id, workspace_id, current_user)
    if version.quest_id != quest_id:
        raise HTTPException(status_code=404, detail="Version not found")
    if version.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft can be deleted")
    svc = EditorService()
    await svc.delete_version(db, version_id)
    await db.commit()
    return {"status": "ok"}


@router.get(
    "/versions/{version_id}/graph",
    response_model=QuestGraphOut,
    summary="Get version graph",
)
async def get_graph(
    version_id: UUID,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_version_access(db, version_id, workspace_id, current_user)
    svc = QuestGraphService()
    v, steps, transitions = await svc.load_graph(db, version_id)
    return QuestGraphOut(
        version=QuestVersionOut.model_validate(v, from_attributes=True),
        steps=steps,
        transitions=transitions,
    )


@router.put(
    "/versions/{version_id}/graph",
    summary="Replace version graph",
)
async def put_graph(
    version_id: UUID,
    payload: QuestGraphIn,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_version_access(db, version_id, workspace_id, current_user)
    svc = QuestGraphService()
    await svc.save_graph(db, version_id, payload.steps, payload.transitions)
    await db.commit()
    return {"ok": True}


@router.post(
    "/versions/{version_id}/validate",
    response_model=ValidateResult,
    summary="Validate version graph",
)
async def validate_version(
    version_id: UUID,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_version_access(db, version_id, workspace_id, current_user)
    svc = EditorService()
    return await svc.validate_version(db, version_id)


@router.post(
    "/versions/{version_id}/simulate",
    response_model=SimulateResult,
    summary="Simulate version graph",
)
async def simulate_version(
    version_id: UUID,
    payload: SimulateIn,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    preview: PreviewContext = Depends(get_preview_context),
):
    await _ensure_version_access(db, version_id, workspace_id, current_user)
    svc = EditorService()
    return await svc.simulate_version(db, version_id, payload, preview)


@router.post(
    "/versions/{version_id}/publish",
    response_model=QuestVersionOut,
    summary="Publish version",
)
async def publish_version(
    version_id: UUID,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await _ensure_version_access(db, version_id, workspace_id, current_user)
    if version.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft can be published")
    svc = EditorService()
    res = await svc.validate_version(db, version_id)
    if not res.ok:
        raise HTTPException(status_code=400, detail={"errors": res.errors})
    version.status = "released"
    version.released_at = datetime.utcnow()
    version.released_by = current_user.id
    await db.commit()
    await db.refresh(version)
    return QuestVersionOut.model_validate(version, from_attributes=True)
