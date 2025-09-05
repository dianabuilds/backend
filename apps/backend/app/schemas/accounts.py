from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.notification_rules import NotificationRules


class AccountRole(str, Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class AccountKind(str, Enum):
    personal = "personal"
    team = "team"


class AccountSettings(BaseModel):
    ai_presets: dict[str, object] = Field(default_factory=dict)
    notifications: NotificationRules = Field(default_factory=NotificationRules)
    limits: dict[str, int] = Field(
        default_factory=lambda: {
            "ai_tokens": 0,
            "notif_per_day": 0,
            "compass_calls": 0,
        }
    )
    features: dict[str, bool] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _ensure_limit_keys(self) -> AccountSettings:
        """Ensure new limit keys always exist."""
        self.limits.setdefault("ai_tokens", 0)
        self.limits.setdefault("notif_per_day", 0)
        self.limits.setdefault("compass_calls", 0)
        self.features = self.features or {}
        return self


class AccountIn(BaseModel):
    name: str
    slug: str | None = None
    settings: AccountSettings = Field(default_factory=AccountSettings)
    kind: AccountKind = AccountKind.team
    is_system: bool = False


class AccountOut(BaseModel):
    id: int
    name: str
    slug: str
    owner_user_id: UUID
    settings: AccountSettings = Field(default_factory=AccountSettings, alias="settings_json")
    kind: AccountKind
    is_system: bool
    created_at: datetime
    updated_at: datetime
    role: AccountRole | None = None

    model_config = ConfigDict(from_attributes=True)


class AccountWithRoleOut(AccountOut):
    role: AccountRole


class AccountUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    settings: AccountSettings | None = None
    kind: AccountKind | None = None
    is_system: bool | None = None


class AccountMemberIn(BaseModel):
    user_id: UUID
    role: AccountRole


class AccountMemberOut(BaseModel):
    account_id: int
    user_id: UUID
    role: AccountRole

    model_config = ConfigDict(from_attributes=True)


class AccountCursorPage(BaseModel):
    """Cursor-paginated list of accounts."""

    limit: int
    sort: str
    order: Literal["asc", "desc"]
    items: list[AccountWithRoleOut]
    next_cursor: str | None = None
