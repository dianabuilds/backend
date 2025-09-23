from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Template:
    id: str
    slug: str
    name: str
    description: str | None
    subject: str | None
    body: str
    locale: str | None
    variables: dict[str, Any] | None
    meta: dict[str, Any] | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime


__all__ = ["Template"]
