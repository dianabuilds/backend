from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class NodeNotificationSettingsOut(BaseModel):
    node_id: int
    node_alt_id: UUID
    enabled: bool

    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, alias_generator=to_camel
    )


class NodeNotificationSettingsUpdate(BaseModel):
    enabled: bool
