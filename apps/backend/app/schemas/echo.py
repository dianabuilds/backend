from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AdminEchoTraceOut(BaseModel):
    id: UUID
    from_slug: str
    to_slug: str
    user_id: UUID | None = None
    source: str | None = None
    channel: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PopularityRecomputeRequest(BaseModel):
    node_slugs: list[str] | None = None
