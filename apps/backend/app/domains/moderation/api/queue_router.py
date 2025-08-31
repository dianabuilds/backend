from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.security import ADMIN_AUTH_RESPONSES, require_admin_role


class QueueItem(BaseModel):
    id: UUID
    type: str
    reason: str
    status: str = "pending"


# simple in-memory queue store for demo purposes
QUEUE: list[QueueItem] = [
    QueueItem(id=uuid4(), type="user", reason="spam"),
    QueueItem(id=uuid4(), type="content", reason="abuse"),
]


admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/moderation",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


def _find_item(item_id: UUID) -> QueueItem:
    for item in QUEUE:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@router.get("/queue", response_model=list[QueueItem])
async def list_queue(
    type: str | None = None, status: str | None = None
) -> list[QueueItem]:
    items = QUEUE
    if type:
        items = [i for i in items if i.type == type]
    if status:
        items = [i for i in items if i.status == status]
    return items


@router.get("/queue/{item_id}", response_model=QueueItem)
async def get_queue_item(item_id: UUID) -> QueueItem:
    return _find_item(item_id)


@router.post("/queue/{item_id}/approve")
async def approve_item(item_id: UUID) -> dict[str, str]:
    item = _find_item(item_id)
    item.status = "approved"
    return {"status": "ok"}


@router.post("/queue/{item_id}/reject")
async def reject_item(item_id: UUID) -> dict[str, str]:
    item = _find_item(item_id)
    item.status = "rejected"
    return {"status": "ok"}
