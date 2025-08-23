from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func

from app.core.db.session import get_db
from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.users.infrastructure.models.user import User
from app.schemas.quest import QuestOut, QuestUpdate
from app.schemas.quest_validation import ValidationReport, AutofixRequest, AutofixReport, PublishRequest
from app.schemas.content_common import ContentStatus
from app.security import ADMIN_AUTH_RESPONSES, require_ws_editor, auth_user
from app.domains.audit.application.audit_service import audit_log
from app.domains.quests.validation import validate_quest

router = APIRouter(
    prefix="/admin/quests",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("", response_model=list[QuestOut], summary="Admin list quests with filters")
async def admin_list_quests(
    workspace_id: UUID,
    q: Optional[str] = None,
    author_role: Optional[str] = Query(None, pattern="^(admin|moderator|user)$"),
    author_id: Optional[UUID] = None,
    draft: Optional[bool] = None,
    deleted: Optional[bool] = None,
    free_only: bool = False,
    premium_only: bool = False,
    length: Optional[str] = Query(None, pattern="^(short|long)$"),
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    sort_by: str = Query("new", pattern="^(new|price|title|popularity)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Quest).where(Quest.workspace_id == workspace_id)
    if draft is not None:
        if draft:
            stmt = stmt.where(Quest.status == ContentStatus.draft)
        else:
            stmt = stmt.where(Quest.status != ContentStatus.draft)
    if deleted is not None:
        stmt = stmt.where(Quest.is_deleted.is_(deleted))
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Quest.title.ilike(pattern),
                Quest.subtitle.ilike(pattern),
                Quest.description.ilike(pattern),
            )
        )
    if free_only:
        stmt = stmt.where(or_(Quest.price == None, Quest.price == 0))  # noqa: E711
    if premium_only:
        stmt = stmt.where(Quest.is_premium_only.is_(True))
    if length:
        stmt = stmt.where(Quest.length == length)
    if created_from:
        stmt = stmt.where(Quest.created_at >= created_from)
    if created_to:
        stmt = stmt.where(Quest.created_at <= created_to)
    if author_id:
        stmt = stmt.where(Quest.author_id == author_id)
    elif author_role:
        stmt = stmt.join(User, User.id == Quest.author_id).where(User.role == author_role)

    if sort_by == "price":
        stmt = stmt.order_by(Quest.price.asc().nullsLast())
    elif sort_by == "title":
        stmt = stmt.order_by(Quest.title.asc())
    elif sort_by == "popularity":
        stmt = stmt.order_by(func.coalesce(Quest.published_at, datetime.min).desc())
    else:
        stmt = stmt.order_by(Quest.created_at.desc())

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{quest_id}/meta", response_model=QuestOut, summary="Get quest metadata")
async def get_quest_meta(
    quest_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> QuestOut:
    q = await db.get(Quest, quest_id)
    if not q or q.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Quest not found")
    return q


@router.patch("/{quest_id}/meta", response_model=QuestOut, summary="Update quest metadata")
async def patch_quest_meta(
    quest_id: UUID,
    workspace_id: UUID,
    body: QuestUpdate,
    request: Request,
    current: User = Depends(auth_user),
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> QuestOut:
    q = await db.get(Quest, quest_id)
    if not q or q.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Quest not found")
    before = {
        "title": q.title,
        "subtitle": q.subtitle,
        "description": q.description,
        "cover_image": q.cover_image,
        "price": q.price,
        "is_premium_only": q.is_premium_only,
        "allow_comments": q.allow_comments,
    }
    # обновляем только переданные поля
    upd = body.model_dump(exclude_unset=True)
    for k, v in upd.items():
        if hasattr(q, k):
            setattr(q, k, v)
    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="quest_meta_update",
        resource_type="quest",
        resource_id=str(quest_id),
        before=before,
        after=upd,
        request=request,
    )
    await db.commit()
    return q


@router.get("/{quest_id}/validation", response_model=ValidationReport, summary="Validate quest")
async def get_quest_validation(
    quest_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> ValidationReport:
    q = await db.get(Quest, quest_id)
    if not q or q.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Quest not found")
    report = await validate_quest(db, q)
    return report


@router.post("/{quest_id}/autofix", response_model=AutofixReport, summary="Apply autofix to quest")
async def post_quest_autofix(
    quest_id: UUID,
    workspace_id: UUID,
    body: AutofixRequest,
    request: Request,
    current: User = Depends(auth_user),
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> AutofixReport:
    q = await db.get(Quest, quest_id)
    if not q or q.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Quest not found")

    actions = set(body.actions or [])
    if not actions:
        # по умолчанию применяем базовые фиксы
        actions = {"ensure_entry", "deduplicate_nodes"}

    applied: list[dict] = []
    skipped: list[dict] = []

    # Исходное состояние
    before = {
        "entry_node_id": str(q.entry_node_id) if q.entry_node_id else None,
        "nodes_count": len(q.nodes or []),
    }

    nodes = list(q.nodes or [])
    changed = False

    # deduplicate_nodes: убрать None и дубликаты, сохранить порядок
    if "deduplicate_nodes" in actions:
        new_nodes = []
        seen = set()
        for n in nodes:
            if n is None:
                continue
            if n in seen:
                continue
            seen.add(n)
            new_nodes.append(n)
        if new_nodes != nodes:
            q.nodes = new_nodes
            nodes = new_nodes
            changed = True
            applied.append({"type": "deduplicate_nodes", "affected": len(before["nodes_count"]) if isinstance(before.get("nodes_count"), list) else 0, "note": None})
        else:
            skipped.append({"type": "deduplicate_nodes", "affected": 0, "note": "no duplicates"})

    # ensure_entry: если entry пуст и есть nodes — назначить первый; если entry есть, но отсутствует в nodes — добавить
    if "ensure_entry" in actions:
        if not q.entry_node_id and nodes:
            q.entry_node_id = nodes[0]
            changed = True
            applied.append({"type": "ensure_entry", "affected": 1, "note": "entry set to first node"})
        elif q.entry_node_id and nodes and q.entry_node_id not in nodes:
            q.nodes = [q.entry_node_id] + nodes
            nodes = q.nodes
            changed = True
            applied.append({"type": "ensure_entry", "affected": 1, "note": "entry added to nodes list"})
        else:
            skipped.append({"type": "ensure_entry", "affected": 0, "note": "entry ok"})

    if changed:
        await db.commit()

    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="quest_autofix",
        resource_type="quest",
        resource_id=str(quest_id),
        before=before,
        after={
            "entry_node_id": str(q.entry_node_id) if q.entry_node_id else None,
            "nodes_count": len(q.nodes or []),
            "applied": applied,
            "skipped": skipped,
        },
        request=request,
    )
    return AutofixReport(
        applied=[type("X", (), x) for x in applied],
        skipped=[type("X", (), x) for x in skipped],
    )


@router.post("/{quest_id}/publish", summary="Publish quest")
async def post_quest_publish(
    quest_id: UUID,
    workspace_id: UUID,
    body: PublishRequest,
    request: Request,
    current: User = Depends(auth_user),
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
):
    q = await db.get(Quest, quest_id)
    if not q or q.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Quest not found")

    # Валидация перед публикацией: ошибки запрещают публикацию
    report = await validate_quest(db, q)
    if report.errors > 0:
        raise HTTPException(status_code=409, detail="Validation errors prevent publishing")

    before = {
        "status": q.status,
        "visibility": q.visibility,
        "published_at": q.published_at.isoformat() if q.published_at else None,
        "cover_image": q.cover_image,
    }

    # Применяем настройки доступа и публикуем
    q.is_premium_only = body.access == "premium_only"
    q.status = ContentStatus.published
    q.published_at = datetime.utcnow()
    if body.cover_url:
        q.cover_image = body.cover_url

    await db.commit()

    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="quest_publish",
        resource_type="quest",
        resource_id=str(quest_id),
        before=before,
        after={"status": q.status, "is_premium_only": q.is_premium_only, "published_at": q.published_at.isoformat()},
        request=request,
        reason=f"access={body.access}",
    )
    return {"status": "published", "quest_id": str(quest_id)}
