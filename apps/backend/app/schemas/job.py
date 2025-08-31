from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BackgroundJobHistoryOut(BaseModel):
    id: UUID
    name: str
    status: str
    log_url: str | None = None
    started_at: datetime
    finished_at: datetime | None = None

    model_config = {"from_attributes": True}
