from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.settings import get_settings
from app.domains.moderation.infrastructure.models.moderation_case_models import (
    CaseAttachment,
    CaseEvent,
    CaseLabel,
    CaseNote,
    ModerationCase,
)
from app.providers.case_notifier import ICaseNotifier
from app.schemas.moderation_cases import (
    CaseAttachmentOut,
    CaseClose,
    CaseCreate,
    CaseEventOut,
    CaseFullResponse,
    CaseListItem,
    CaseListResponse,
    CaseNoteCreate,
    CaseNoteOut,
    CaseOut,
    CasePatch,
)


class CasesService:
    async def list_cases(
        self,
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        statuses: list[str] | None = None,
    ) -> CaseListResponse:
        stmt = select(ModerationCase)
        if statuses:
            stmt = stmt.where(ModerationCase.status.in_(statuses))
        stmt = (
            stmt.order_by(ModerationCase.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .options(selectinload(ModerationCase.labels).selectinload(CaseLabel.label))
        )
        res = await db.execute(stmt)
        cases = res.scalars().all()

        total_stmt = select(func.count()).select_from(ModerationCase)
        if statuses:
            total_stmt = total_stmt.where(ModerationCase.status.in_(statuses))
        total = await db.scalar(total_stmt)

        items = [
            CaseListItem(
                id=c.id,
                type=c.type,
                status=c.status,
                priority=c.priority,
                summary=c.summary,
                target_type=c.target_type,
                target_id=c.target_id,
                assignee_id=c.assignee_id,
                labels=[cl.label.name for cl in c.labels],
                created_at=c.created_at,
                due_at=c.due_at,
                last_event_at=c.last_event_at,
            )
            for c in cases
        ]
        return CaseListResponse(items=items, page=page, size=size, total=total or 0)

    async def create_case(
        self, db: AsyncSession, data: CaseCreate, notifier: ICaseNotifier | None = None
    ) -> UUID:
        settings = get_settings().moderation
        now = datetime.utcnow()
        case = ModerationCase(
            **data.model_dump(exclude={"labels", "attachments"}),
            first_response_due_at=now + settings.first_response_delta(),
            due_at=now + settings.resolution_delta(),
            last_event_at=now,
        )
        db.add(case)
        await db.flush()

        for att in data.attachments or []:
            db.add(
                CaseAttachment(
                    case_id=case.id,
                    author_id=data.reporter_id,
                    **att.model_dump(),
                )
            )

        await db.commit()
        await db.refresh(case)
        if notifier:
            await notifier.case_created(case.id)
        return case.id

    async def patch_case(
        self, db: AsyncSession, case_id: UUID, patch: CasePatch
    ) -> CaseOut | None:
        case = await db.get(ModerationCase, case_id)
        if not case:
            return None
        updates = patch.model_dump(exclude_none=True)
        now = datetime.utcnow()
        events: list[CaseEvent] = []
        if "assignee_id" in updates and updates["assignee_id"] != case.assignee_id:
            case.assignee_id = updates["assignee_id"]
            events.append(
                CaseEvent(
                    case_id=case.id,
                    kind="assign",
                    payload={"assignee_id": str(updates["assignee_id"])}
                )
            )
        if "status" in updates and updates["status"] != case.status:
            case.status = updates["status"]
            events.append(
                CaseEvent(
                    case_id=case.id,
                    kind="status_change",
                    payload={"status": updates["status"]},
                )
            )
        for field in set(updates) - {"assignee_id", "status"}:
            setattr(case, field, updates[field])
        if events:
            case.last_event_at = now
            db.add_all(events)
        case.updated_at = now
        await db.commit()
        await db.refresh(case, attribute_names=["labels"])
        return self._to_case_out(case)

    async def add_note(
        self,
        db: AsyncSession,
        case_id: UUID,
        note: CaseNoteCreate,
        author_id: UUID | None,
    ) -> CaseNoteOut | None:
        case = await db.get(ModerationCase, case_id)
        if not case:
            return None
        note_obj = CaseNote(
            case_id=case_id,
            author_id=author_id,
            text=note.text,
            internal=note.internal if note.internal is not None else True,
        )
        db.add(note_obj)
        await db.flush()
        event = CaseEvent(
            case_id=case_id,
            actor_id=author_id,
            kind="add_note",
            payload={"note_id": str(note_obj.id)},
        )
        db.add(event)
        case.last_event_at = datetime.utcnow()
        await db.commit()
        await db.refresh(note_obj)
        return CaseNoteOut.model_validate(note_obj, from_attributes=True)

    async def close_case(
        self,
        db: AsyncSession,
        case_id: UUID,
        payload: CaseClose,
        actor_id: UUID | None,
    ) -> CaseOut | None:
        case = await db.get(ModerationCase, case_id)
        if not case:
            return None
        case.status = "resolved" if payload.resolution == "resolved" else "rejected"
        case.resolution = payload.resolution
        case.reason_code = payload.reason_code
        now = datetime.utcnow()
        event = CaseEvent(
            case_id=case.id,
            actor_id=actor_id,
            kind="status_change",
            payload={"status": case.status, "resolution": case.resolution},
        )
        db.add(event)
        case.last_event_at = now
        await db.commit()
        await db.refresh(case)
        return self._to_case_out(case)

    async def get_case(
        self, db: AsyncSession, case_id: UUID
    ) -> CaseFullResponse | None:
        stmt = (
            select(ModerationCase)
            .where(ModerationCase.id == case_id)
            .options(
                selectinload(ModerationCase.labels).selectinload(CaseLabel.label),
                selectinload(ModerationCase.notes),
                selectinload(ModerationCase.attachments),
                selectinload(ModerationCase.events),
            )
        )
        res = await db.execute(stmt)
        case = res.scalar_one_or_none()
        if not case:
            return None
        return CaseFullResponse(
            case=self._to_case_out(case),
            notes=[
                CaseNoteOut.model_validate(n, from_attributes=True) for n in case.notes
            ],
            attachments=[
                CaseAttachmentOut.model_validate(a, from_attributes=True)
                for a in case.attachments
            ],
            events=[
                CaseEventOut.model_validate(e, from_attributes=True)
                for e in case.events
            ],
        )

    def _to_case_out(self, case: ModerationCase) -> CaseOut:
        return CaseOut(
            id=case.id,
            created_at=case.created_at,
            updated_at=case.updated_at,
            type=case.type,
            status=case.status,
            priority=case.priority,
            reporter_id=case.reporter_id,
            reporter_contact=case.reporter_contact,
            target_type=case.target_type,
            target_id=case.target_id,
            summary=case.summary,
            details=case.details,
            assignee_id=case.assignee_id,
            due_at=case.due_at,
            first_response_due_at=case.first_response_due_at,
            last_event_at=case.last_event_at,
            source=case.source,
            reason_code=case.reason_code,
            resolution=case.resolution,
            labels=[cl.label.name for cl in case.labels],
        )
