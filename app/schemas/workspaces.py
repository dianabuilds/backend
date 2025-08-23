from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WorkspaceIn(BaseModel):
    name: str
    slug: str | None = None
    settings: dict[str, object] = Field(default_factory=dict)


class WorkspaceOut(BaseModel):
    id: UUID
    name: str
    slug: str
    owner_user_id: UUID
    settings: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    settings: dict[str, object] | None = None


class WorkspaceMemberIn(BaseModel):
    user_id: UUID
    role: str


class WorkspaceMemberOut(BaseModel):
    workspace_id: UUID
    user_id: UUID
    role: str

    class Config:
        orm_mode = True
