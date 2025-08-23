from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class WorkspaceRole(str, Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class WorkspaceType(str, Enum):
    personal = "personal"
    team = "team"
    global_ = "global"


class WorkspaceIn(BaseModel):
    name: str
    slug: str | None = None
    settings: dict[str, object] = Field(default_factory=dict)
    type: WorkspaceType = WorkspaceType.team
    is_system: bool = False


class WorkspaceOut(BaseModel):
    id: UUID
    name: str
    slug: str
    owner_user_id: UUID
    settings: dict[str, object] = Field(default_factory=dict)
    type: WorkspaceType
    is_system: bool
    created_at: datetime
    updated_at: datetime
    role: WorkspaceRole | None = None

    class Config:
        orm_mode = True


class WorkspaceWithRoleOut(WorkspaceOut):
    role: WorkspaceRole


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    settings: dict[str, object] | None = None
    type: WorkspaceType | None = None
    is_system: bool | None = None


class WorkspaceMemberIn(BaseModel):
    user_id: UUID
    role: WorkspaceRole


class WorkspaceMemberOut(BaseModel):
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole

    class Config:
        orm_mode = True
