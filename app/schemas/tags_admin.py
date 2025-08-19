from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TagListItem(BaseModel):
    id: UUID
    slug: str
    name: str
    created_at: datetime
    usage_count: int = 0
    aliases_count: int = 0
    is_hidden: bool = False

    model_config = {"from_attributes": True}


class TagOut(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None = None
    color: str | None = None
    is_hidden: bool = False
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class AliasOut(BaseModel):
    id: UUID
    alias: str
    type: str

    model_config = {"from_attributes": True}


class MergeIn(BaseModel):
    from_id: UUID
    to_id: UUID
    dryRun: bool = True
    reason: str | None = None


class MergeReport(BaseModel):
    from_: dict[str, Any] = Field(alias="from")
    to: dict[str, Any]
    content_touched: int
    aliases_moved: int
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class BlacklistItem(BaseModel):
    slug: str
    reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BlacklistAdd(BaseModel):
    slug: str
    reason: str | None = None
