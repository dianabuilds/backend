from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel
from pydantic import AliasChoices
from pydantic import model_validator
from typing import Literal


class NodeBase(BaseModel):
    # Названия полей, приходящие из админки, могут отличаться:
    # - contentData -> content
    # - allow_comments -> allow_feedback
    # - is_premium_only -> premium_only
    title: str | None = None
    # Контент всегда Editor.js JSON, поле формата нам не нужно
    content: Any = Field(..., validation_alias=AliasChoices("content", "contentData"))
    media: list[str] | None = None
    cover_url: str | None = None
    tags: list[str] | None = None
    is_public: bool = False
    is_visible: bool = True
    meta: dict = Field(default_factory=dict)
    premium_only: bool | None = Field(
        default=None, validation_alias=AliasChoices("premium_only", "is_premium_only")
    )
    nft_required: str | None = None
    ai_generated: bool | None = None
    allow_feedback: bool = Field(
        default=True, validation_alias=AliasChoices("allow_feedback", "allow_comments")
    )
    is_recommendable: bool = True

    class Config:
        alias_generator = to_camel
        populate_by_name = True  # позволяем заполнять по исходным именам и алиасам

    @model_validator(mode="after")
    def _normalize_editorjs_and_validate(self) -> "NodeBase":
        # Приводим контент к Editor.js JSON: допускаем строковый JSON
        if isinstance(self.content, str):
            import json
            try:
                self.content = json.loads(self.content)
            except Exception:
                raise ValueError("content must be valid JSON for Editor.js")
        if not isinstance(self.content, (dict, list)):
            raise ValueError("content must be an object or array for Editor.js")
        # Нормализуем списки
        if self.media is not None and not (isinstance(self.media, list) and all(isinstance(x, str) for x in self.media)):
            raise ValueError("media must be an array of strings")
        if self.cover_url is not None and not isinstance(self.cover_url, str):
            raise ValueError("cover_url must be a string")
        if self.tags is not None and not (isinstance(self.tags, list) and all(isinstance(x, str) for x in self.tags)):
            raise ValueError("tags must be an array of strings")
        return self


class NodeCreate(NodeBase):
    pass


class NodeUpdate(BaseModel):
    title: str | None = None
    content: Any | None = Field(
        default=None, validation_alias=AliasChoices("content", "contentData")
    )
    media: list[str] | None = None
    cover_url: str | None = None
    tags: list[str] | None = None
    is_public: bool | None = None
    is_visible: bool | None = None
    allow_feedback: bool | None = Field(
        default=None, validation_alias=AliasChoices("allow_feedback", "allow_comments")
    )
    is_recommendable: bool | None = None
    premium_only: bool | None = Field(
        default=None, validation_alias=AliasChoices("premium_only", "is_premium_only")
    )
    nft_required: str | None = None
    ai_generated: bool | None = None


class NodeOut(NodeBase):
    tags: list[str] = Field(default_factory=list, validation_alias="tag_slugs")
    id: UUID
    slug: str
    author_id: UUID
    views: int
    reactions: dict[str, int]
    created_at: datetime
    updated_at: datetime
    popularity_score: float

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def _normalize_output(self) -> "NodeOut":
        # Приводим popularity_score к числу (некорректные значения -> 0.0)
        try:
            # если пришло строкой или иным типом — пробуем привести
            self.popularity_score = float(self.popularity_score)  # type: ignore[arg-type]
        except Exception:
            self.popularity_score = 0.0
        # Приводим reactions к словарю
        if not isinstance(self.reactions, dict):
            try:
                # попробуем распарсить строку/список в словарь-частоты
                import json
                if isinstance(self.reactions, str):
                    parsed = json.loads(self.reactions)
                    if isinstance(parsed, dict):
                        self.reactions = {str(k): int(v) for k, v in parsed.items()}
                    else:
                        self.reactions = {}
                else:
                    self.reactions = {}
            except Exception:
                self.reactions = {}
        return self


class ReactionUpdate(BaseModel):
    reaction: str
    action: Literal["add", "remove"]


class NodeBulkOperation(BaseModel):
    """Payload for bulk node admin operations."""

    ids: list[UUID]
    op: Literal[
        "hide",
        "show",
        "public",
        "private",
        "toggle_premium",
        "toggle_recommendable",
    ]
