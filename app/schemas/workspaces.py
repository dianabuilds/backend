from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field


WorkspaceRole = Literal["owner", "editor", "viewer"]


class WorkspaceIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str | None = Field(default=None, max_length=200)
    settings: dict[str, Any] = Field(default_factory=dict)


class WorkspaceOut(BaseModel):
    id: UUID
    name: str
    slug: str
    owner_user_id: UUID | None
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    settings: dict[str, Any] | None = None


class WorkspaceMemberIn(BaseModel):
    user_id: UUID
    role: WorkspaceRole = "editor"


class WorkspaceMemberOut(BaseModel):
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole
    created_at: datetime
