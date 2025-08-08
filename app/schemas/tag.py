from pydantic import BaseModel, Field


class TagOut(BaseModel):
    slug: str
    name: str
    count: int = 0


class NodeTagsUpdate(BaseModel):
    tags: list[str] = Field(default_factory=list)
