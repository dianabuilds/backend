from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class ValidationItem(BaseModel):
    level: Literal["error", "warning", "info"]
    code: str
    message: str
    node_id: UUID | None = None
    hint: str | None = None


class ValidationReport(BaseModel):
    errors: int
    warnings: int
    items: list[ValidationItem]


class AutofixRequest(BaseModel):
    actions: list[str] = []  # e.g. ["mark_endings","remove_broken_links"]


class AutofixResult(BaseModel):
    type: str
    affected: int
    note: str | None = None


class AutofixReport(BaseModel):
    applied: list[AutofixResult] = []
    skipped: list[AutofixResult] = []


class PublishRequest(BaseModel):
    access: Literal["premium_only", "everyone", "early_access"] = "everyone"
    cover_url: str | None = None
    style_preset: str | None = None
