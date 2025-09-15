from __future__ import annotations

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.moderation.application import CasesService as MonoCasesService


class ModerationRepoAdapter:
    """Adapter that delegates to the monolith Moderation CasesService.

    This keeps DDD API thin while reusing existing logic and schema.
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._svc = MonoCasesService()

    async def list_cases(self, *, page: int, size: int, statuses: Sequence[str] | None = None) -> dict:
        res = await self._svc.list_cases(self._db, page=page, size=size, statuses=list(statuses) if statuses else None)
        return res.model_dump() if hasattr(res, "model_dump") else dict(res)

    async def create_case(self, payload: dict) -> str:
        from app.schemas.moderation_cases import CaseCreate

        obj = CaseCreate(**payload)
        cid = await self._svc.create_case(self._db, obj, notifier=None)
        return str(cid)

    async def add_note(self, case_id: str, note: dict, *, author_id: str | None) -> dict | None:
        from uuid import UUID
        from app.schemas.moderation_cases import CaseNoteCreate

        n = CaseNoteCreate(**note)
        out = await self._svc.add_note(self._db, UUID(case_id), n, UUID(author_id) if author_id else None)
        return out.model_dump() if out is not None and hasattr(out, "model_dump") else (dict(out) if out else None)

