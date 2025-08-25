from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.notification_rules import NotificationRules


class WorkspaceRole(str, Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class WorkspaceType(str, Enum):
    personal = "personal"
    team = "team"
    global_ = "global"


class WorkspaceSettings(BaseModel):
    ai_presets: dict[str, object] = Field(default_factory=dict)
    notifications: NotificationRules = Field(default_factory=NotificationRules)
    limits: dict[str, int] = Field(
        default_factory=lambda: {
            "ai_tokens": 0,
            "notif_per_day": 0,
            "compass_calls": 0,
        }
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _ensure_limit_keys(self) -> WorkspaceSettings:
        """Ensure new limit keys always exist."""
        self.limits.setdefault("ai_tokens", 0)
        self.limits.setdefault("notif_per_day", 0)
        self.limits.setdefault("compass_calls", 0)
        return self


class WorkspaceIn(BaseModel):
    name: str
    slug: str | None = None
    settings: WorkspaceSettings = Field(default_factory=WorkspaceSettings)
    type: WorkspaceType = WorkspaceType.team
    is_system: bool = False


class WorkspaceOut(BaseModel):
    id: UUID
    name: str
    slug: str
    owner_user_id: UUID
    settings: WorkspaceSettings = Field(
        default_factory=WorkspaceSettings, alias="settings_json"
    )
    type: WorkspaceType
    is_system: bool
    created_at: datetime
    updated_at: datetime
    role: WorkspaceRole | None = None

    model_config = ConfigDict(from_attributes=True)


class WorkspaceWithRoleOut(WorkspaceOut):
    role: WorkspaceRole


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    settings: WorkspaceSettings | None = None
    type: WorkspaceType | None = None
    is_system: bool | None = None


class WorkspaceMemberIn(BaseModel):
    user_id: UUID
    role: WorkspaceRole


class WorkspaceMemberOut(BaseModel):
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole

    model_config = ConfigDict(from_attributes=True)
