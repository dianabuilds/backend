from __future__ import annotations

from typing import Literal
from uuid import UUID
from pydantic import BaseModel


ContentStatus = Literal["draft", "in_review", "published", "archived"]
ContentVisibility = Literal["private", "unlisted", "public"]


class ContentMeta(BaseModel):
    workspace_id: UUID
    status: ContentStatus = "draft"
    version: int = 1
    visibility: ContentVisibility = "private"
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None
