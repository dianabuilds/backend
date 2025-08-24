from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class NodeNotificationSettingsOut(BaseModel):
    node_id: UUID
    enabled: bool

    model_config = {"from_attributes": True}


class NodeNotificationSettingsUpdate(BaseModel):
    enabled: bool
