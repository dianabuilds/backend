from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AchievementOut(BaseModel):
    id: UUID
    code: str
    title: str
    description: str | None = None
    icon: str | None = None
    unlocked: bool
    unlocked_at: datetime | None = None


class AchievementAdminOut(BaseModel):
    id: UUID
    code: str
    title: str
    description: str | None = None
    icon: str | None = None
    visible: bool
    condition: dict[str, Any]
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None


class AchievementCreateIn(BaseModel):
    code: str
    title: str
    description: str | None = None
    icon: str | None = None
    visible: bool = True
    condition: dict[str, Any] = {}


class AchievementUpdateIn(BaseModel):
    code: str | None = None
    title: str | None = None
    description: str | None = None
    icon: str | None = None
    visible: bool | None = None
    condition: dict[str, Any] | None = None
