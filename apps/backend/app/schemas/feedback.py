from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FeedbackBase(BaseModel):
    content: str
    is_anonymous: bool = False


class FeedbackCreate(FeedbackBase):
    pass


class FeedbackOut(FeedbackBase):
    id: UUID
    node_id: UUID
    author_id: UUID
    created_at: datetime
    is_hidden: bool

    model_config = {"from_attributes": True}
