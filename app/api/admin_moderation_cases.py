from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select, and_, or_, literal
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.moderation_case import (
    ModerationCase,
    ModerationLabel,
    CaseLabel,
    CaseNote,
    CaseAttachment,
    CaseEvent,
)
from app.models.user import User
from app.schemas.moderation_cases import (
    CaseListItem,
    CaseListResponse,
    CaseCreateIn,
    CasePatchIn,
    CaseFull,
    CaseNoteOut,
    CaseNoteCreateIn,
    CaseAttachmentOut,
    CaseAttachmentCreateIn,
    CaseEventOut,
    CloseCaseIn,
    EscalateIn,
    LabelsPatchIn,
)
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.services.audit import audit_log

admin_required = require_admin_role({"admin", "moderator"})

router = APIRouter(
    prefix="/admin/moderation",
    tags=["moderation"],
    responses=ADMIN_AUTH_RESPONSES,
)


def _status_transition_allowed(cur: str, new: str) -> bool:
    if cur == new:
        return True
    active = {"new", "assigned", "in_progress", "waiting_user", "escalated"}
    finals = {"resolved", "rejected"}
    transitions = {
        "new": {"assigned", "rejected"},
        "assigned": {"in_progress", "waiting_user", "resolved", "rejected", "escalated"},
        "in_progress": {"waiting_user", "resolved", "rejected", "escalated"},
        "waiting_user": {"in_progress", "resolved", "rejected"},
        "escalated": {"in_progress", "resolved", "rejected"},
    }
    if cur in transitions and new in transitions[cur]:
        return True
    # Любой активный -> финальные
    if cur in active and new in finals:
        return True
    # Финальные можно переоткрыть только отдельной операцией
    return False


@router.get("/cases", response_model=CaseListResponse, summary="List moderation cases")
async def list_cases(
    q: str | None = None,
    status: List[str] = Query(default_factory=list),
    type: List[str] = Query(default_factory=list),
    priority: List[str] = Query(default_factory=list),
    label: List[str] = Query(default_factory=list),
    assignee_id: UUID | None = None,
    reporter_id: UUID | None = None,
    target_type: str | None = None,
    overdue: bool | None = None,
    page: int = 1,
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
) -> CaseListResponse:
    stmt = select(ModerationCase)
    conds = []
    if q:
        like = f"%{q}%"
        conds.append(or_(ModerationCase.summary.ilike(like), ModerationCase.target_id.ilike(like)))
    if status:
        conds.append(ModerationCase.status.in_(status))
    if type:
        conds.append(ModerationCase.type.in_(type))
    if priority:
        conds.append(ModerationCase.priority.in_(priority))
    if assignee_id:
        conds.append(ModerationCase.assignee_id == assignee_id)
    if reporter_id:
        conds.append(ModerationCase.reporter_id == reporter_id)
    if target_type:
        conds.append(ModerationCase.target_type == target_type)
    if overdue:
        conds.append(and_(ModerationCase.due_at.is_not(None), ModerationCase.due_at < func.now(), ModerationCase.status.not_in(["resolved", "rejected"])))  # type: ignore[attr-defined]
    if conds:
        stmt = stmt.where(and_(*conds))
    total = (await db.execute(stmt.with_only_columns(func.count(literal(1))))).scalar() or 0
    stmt = stmt.order_by(ModerationCase.created_at.desc()).offset((page - 1) * size).limit(size)
    rows = list((await db.execute(stmt)).scalars().all())

    # Соберём лейблы
    ids = [r.id for r in rows]
    labels_map: dict[UUID, list[str]] = {rid: [] for rid in ids}
    if ids:
        join_stmt = (
            select(CaseLabel.case_id, ModerationLabel.name)
            .join(ModerationLabel, ModerationLabel.id == CaseLabel.label_id)
            .where(CaseLabel.case_id.in_(ids))
        )
        for cid, name in (await db.execute(join_stmt)).all():
            labels_map[cid].append(name)

    items: list[CaseListItem] = []
    for r in rows:
        items.append(
            CaseListItem(
                id=r.id,
                type=r.type,
                status=r.status,
                priority=r.priority,
                summary=r.summary,
                target_type=r.target_type,
                target_id=r.target_id,
                assignee_id=r.assignee_id,
                labels=labels_map.get(r.id, []),
                created_at=r.created_at,
                due_at=r.due_at,
                last_event_at=r.last_event_at,
            )
        )

    return CaseListResponse(items=items, page=page, size=size, total=int(total))


@router.post("/cases", summary="Create moderation case")
async def create_case(
    body: CaseCreateIn,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    case = ModerationCase(
        type=body.type,
        status="assigned" if body.assignee_id else "new",
        priority=body.priority or "P2",
        reporter_id=body.reporter_id,
        reporter_contact=body.reporter_contact,
        target_type=body.target_type,
        target_id=body.target_id,
        summary=body.summary,
        details=body.details,
        assignee_id=body.assignee_id,
        source="web",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(case)
    await db.flush()

    # Лейблы
    if body.labels:
        existing = dict((name, lid) for lid, name in (await db.execute(select(ModerationLabel.id, ModerationLabel.name).where(ModerationLabel.name.in_(body.labels)))).all())
        for name in body.labels:
            lid = existing.get(name)
            if not lid:
                label = ModerationLabel(name=name)
                db.add(label)
                await db.flush()
                lid = label.id
            db.add(CaseLabel(case_id=case.id, label_id=lid))

    # Событие
    db.add(CaseEvent(case_id=case.id, actor_id=current_user.id, kind="create", payload=None))

    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="moderation_case_create",
        resource_type="moderation_case",
        resource_id=str(case.id),
        after={"summary": case.summary, "type": case.type, "priority": case.priority},
        request=request,
    )

    return {"id": str(case.id)}


@router.get("/cases/{case_id}", response_model=dict, summary="Get case with details")
async def get_case(
    case_id: UUID,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(ModerationCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # labels
    lbls = (
        await db.execute(
            select(ModerationLabel.name)
            .join(CaseLabel, CaseLabel.label_id == ModerationLabel.id)
            .where(CaseLabel.case_id == case_id)
        )
    ).scalars().all()
    # notes
    notes = (await db.execute(select(CaseNote).where(CaseNote.case_id == case_id).order_by(CaseNote.created_at.desc()))).scalars().all()
    # attachments
    atts = (await db.execute(select(CaseAttachment).where(CaseAttachment.case_id == case_id).order_by(CaseAttachment.created_at.desc()))).scalars().all()
    # events
    evs = (await db.execute(select(CaseEvent).where(CaseEvent.case_id == case_id).order_by(CaseEvent.created_at.desc()))).scalars().all()

    full = CaseFull.model_validate(
        {
            **{c.name: getattr(case, c.name) for c in case.__table__.columns},  # type: ignore[attr-defined]
            "labels": list(lbls),
        }
    )
    return {
        "case": full.model_dump(),
        "notes": [CaseNoteOut.model_validate(n).model_dump() for n in notes],
        "attachments": [CaseAttachmentOut.model_validate(a).model_dump() for a in atts],
        "events": [CaseEventOut.model_validate(e).model_dump() for e in evs],
    }


@router.patch("/cases/{case_id}", summary="Patch case fields")
async def patch_case(
    case_id: UUID,
    body: CasePatchIn,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(ModerationCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    before = {"status": case.status, "priority": case.priority, "assignee_id": str(case.assignee_id) if case.assignee_id else None}

    if body.status and not _status_transition_allowed(case.status, body.status):
        raise HTTPException(status_code=400, detail="Invalid status transition")

    changed = False
    if body.summary is not None:
        case.summary = body.summary
        changed = True
    if body.details is not None:
        case.details = body.details
        changed = True
    if body.priority is not None:
        case.priority = body.priority
        db.add(CaseEvent(case_id=case.id, actor_id=current_user.id, kind="change_priority", payload={"to": body.priority}))
        changed = True
    if body.assignee_id is not None:
        case.assignee_id = body.assignee_id
        db.add(CaseEvent(case_id=case.id, actor_id=current_user.id, kind="assign", payload={"assignee_id": str(body.assignee_id) if body.assignee_id else None}))
        changed = True
    if body.status is not None and body.status != case.status:
        db.add(CaseEvent(case_id=case.id, actor_id=current_user.id, kind="status_change", payload={"from": case.status, "to": body.status}))
        case.status = body.status
        changed = True
    if body.due_at is not None:
        case.due_at = body.due_at
        changed = True

    if changed:
        case.updated_at = datetime.utcnow()
        await audit_log(
            db,
            actor_id=str(current_user.id),
            action="moderation_case_patch",
            resource_type="moderation_case",
            resource_id=str(case.id),
            before=before,
            after={"status": case.status, "priority": case.priority, "assignee_id": str(case.assignee_id) if case.assignee_id else None},
            request=request,
        )

    return {"ok": True}


@router.post("/cases/{case_id}/assign", summary="Assign case")
async def assign_case(
    case_id: UUID,
    assignee_id: UUID,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(ModerationCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    before = {"assignee_id": str(case.assignee_id) if case.assignee_id else None}
    case.assignee_id = assignee_id
    case.status = case.status if case.status != "new" else "assigned"
    case.updated_at = datetime.utcnow()
    db.add(CaseEvent(case_id=case.id, actor_id=current_user.id, kind="assign", payload={"assignee_id": str(assignee_id)}))
    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="moderation_case_assign",
        resource_type="moderation_case",
        resource_id=str(case.id),
        before=before,
        after={"assignee_id": str(assignee_id)},
        request=request,
    )
    return {"ok": True}


@router.post("/cases/{case_id}/notes", response_model=CaseNoteOut, summary="Add note")
async def add_note(
    case_id: UUID,
    body: CaseNoteCreateIn,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(ModerationCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    note = CaseNote(case_id=case_id, author_id=current_user.id, text=body.text, internal=bool(body.internal))
    db.add(note)
    db.add(CaseEvent(case_id=case_id, actor_id=current_user.id, kind="add_note", payload=None))
    await db.flush()
    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="moderation_case_add_note",
        resource_type="moderation_case",
        resource_id=str(case.id),
        after={"note_id": str(note.id)},
        request=request,
    )
    return note  # model_config from_attributes True


@router.post("/cases/{case_id}/attachments", response_model=CaseAttachmentOut, summary="Add attachment")
async def add_attachment(
    case_id: UUID,
    body: CaseAttachmentCreateIn,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(ModerationCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    att = CaseAttachment(case_id=case_id, author_id=current_user.id, url=body.url, title=body.title, media_type=body.media_type)
    db.add(att)
    db.add(CaseEvent(case_id=case_id, actor_id=current_user.id, kind="add_attachment", payload={"url": body.url}))
    await db.flush()
    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="moderation_case_add_attachment",
        resource_type="moderation_case",
        resource_id=str(case.id),
        after={"attachment_id": str(att.id)},
        request=request,
    )
    return att


@router.post("/cases/{case_id}/labels", summary="Patch labels")
async def patch_labels(
    case_id: UUID,
    body: LabelsPatchIn,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(ModerationCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    added: list[str] = []
    removed: list[str] = []

    if body.add:
        existing = dict((name, lid) for lid, name in (await db.execute(select(ModerationLabel.id, ModerationLabel.name).where(ModerationLabel.name.in_(body.add)))).all())
        for name in body.add:
            lid = existing.get(name)
            if not lid:
                label = ModerationLabel(name=name)
                db.add(label)
                await db.flush()
                lid = label.id
            db.add(CaseLabel(case_id=case.id, label_id=lid))
            added.append(name)

    if body.remove:
        # удалить соответствующие связи
        join = (
            select(CaseLabel)
            .join(ModerationLabel, ModerationLabel.id == CaseLabel.label_id)
            .where(CaseLabel.case_id == case.id, ModerationLabel.name.in_(body.remove))
        )
        for cl in (await db.execute(join)).scalars().all():
            removed.append(cl.label.name)  # type: ignore[union-attr]
            await db.delete(cl)

    if added:
        db.add(CaseEvent(case_id=case.id, actor_id=current_user.id, kind="add_label", payload={"labels": added}))
    if removed:
        db.add(CaseEvent(case_id=case.id, actor_id=current_user.id, kind="remove_label", payload={"labels": removed}))

    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="moderation_case_labels",
        resource_type="moderation_case",
        resource_id=str(case.id),
        after={"add": added, "remove": removed},
        request=request,
    )

    return {"ok": True}


@router.post("/cases/{case_id}/actions/close", summary="Close case")
async def close_case(
    case_id: UUID,
    body: CloseCaseIn,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(ModerationCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.status in ("resolved", "rejected"):
        raise HTTPException(status_code=400, detail="Already closed")
    if body.resolution not in ("resolved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid resolution")

    before = {"status": case.status, "resolution": case.resolution, "reason_code": case.reason_code}
    case.status = body.resolution
    case.resolution = body.resolution
    case.reason_code = body.reason_code or body.reason_text or None
    case.updated_at = datetime.utcnow()
    db.add(CaseEvent(case_id=case.id, actor_id=current_user.id, kind="status_change", payload={"to": body.resolution, "reason_code": body.reason_code, "reason_text": body.reason_text}))
    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="moderation_case_close",
        resource_type="moderation_case",
        resource_id=str(case.id),
        before=before,
        after={"status": case.status, "resolution": case.resolution, "reason_code": case.reason_code},
        request=request,
    )
    return {"ok": True}


@router.post("/cases/{case_id}/actions/reopen", summary="Reopen case")
async def reopen_case(
    case_id: UUID,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(ModerationCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.status not in ("resolved", "rejected"):
        raise HTTPException(status_code=400, detail="Not closed")
    before = {"status": case.status}
    case.status = "assigned" if case.assignee_id else "new"
    case.resolution = None
    case.reason_code = None
    case.updated_at = datetime.utcnow()
    db.add(CaseEvent(case_id=case.id, actor_id=current_user.id, kind="reopen", payload=None))
    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="moderation_case_reopen",
        resource_type="moderation_case",
        resource_id=str(case.id),
        before=before,
        after={"status": case.status},
        request=request,
    )
    return {"ok": True}


@router.post("/cases/{case_id}/actions/escalate", summary="Escalate case")
async def escalate_case(
    case_id: UUID,
    body: EscalateIn,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(ModerationCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    before = {"status": case.status}
    case.status = "escalated"
    case.updated_at = datetime.utcnow()
    db.add(CaseEvent(case_id=case.id, actor_id=current_user.id, kind="escalate", payload={"to_role": body.to_role, "reason_text": body.reason_text}))
    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="moderation_case_escalate",
        resource_type="moderation_case",
        resource_id=str(case.id),
        before=before,
        after={"status": case.status},
        request=request,
    )
    return {"ok": True}
