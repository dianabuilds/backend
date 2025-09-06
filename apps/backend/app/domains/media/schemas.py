from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel


class MediaAssetOut(BaseModel):
    id: UUID
    url: str
    type: str
    metadata_json: dict[str, Any] | None = None

    model_config = {"from_attributes": True}
