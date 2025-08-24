from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel


class NodeBase(BaseModel):
    # Названия полей, приходящие из админки, могут отличаться:
    # - contentData -> nodes
    # - allow_comments -> allow_feedback
    # - is_premium_only -> premium_only
    title: str | None = None
    # Контент всегда Editor.js JSON, поле формата нам не нужно
    content: Any = Field(..., validation_alias=AliasChoices("nodes", "contentData"))
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

    @field_validator("meta", mode="before")
    @classmethod
    def _parse_meta(cls, v: Any) -> dict:  # noqa: ANN001
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            import json

            try:
                parsed = json.loads(v)
            except Exception:
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    @model_validator(mode="after")
    def _normalize_editorjs_and_validate(self) -> NodeBase:
        # Приводим контент к Editor.js JSON: допускаем строковый JSON
        if isinstance(self.content, str):
            import json

            try:
                self.content = json.loads(self.content)
            except Exception as err:
                raise ValueError("nodes must be valid JSON for Editor.js") from err
        if not isinstance(self.content, (dict, list)):
            raise ValueError("nodes must be an object or array for Editor.js")
        # Нормализуем списки
        if self.media is not None and not (
            isinstance(self.media, list) and all(isinstance(x, str) for x in self.media)
        ):
            raise ValueError("media must be an array of strings")
        if self.cover_url is not None and not isinstance(self.cover_url, str):
            raise ValueError("cover_url must be a string")
        if self.tags is not None and not (
            isinstance(self.tags, list) and all(isinstance(x, str) for x in self.tags)
        ):
            raise ValueError("tags must be an array of strings")
        return self


class NodeCreate(NodeBase):
    pass


class NodeUpdate(BaseModel):
    title: str | None = None
    content: Any | None = Field(
        default=None, validation_alias=AliasChoices("nodes", "contentData")
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
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None
    views: int
    reactions: dict[str, int] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    popularity_score: float
    quest_data: dict[str, Any] | None = None

    model_config = {"from_attributes": True}

    @field_validator("reactions", mode="before")
    @classmethod
    def _parse_reactions(cls, v: Any) -> dict[str, int]:  # noqa: ANN001
        if v is None:
            return {}
        if isinstance(v, dict):
            try:
                return {str(k): int(vv) for k, vv in v.items()}
            except Exception:
                return {}
        if isinstance(v, str):
            import json

            try:
                parsed = json.loads(v)
            except Exception:
                return {}
            if isinstance(parsed, dict):
                try:
                    return {str(k): int(vv) for k, vv in parsed.items()}
                except Exception:
                    return {}
            return {}
        return {}

    @model_validator(mode="after")
    def _normalize_output(self) -> NodeOut:
        # Приводим popularity_score к числу (некорректные значения -> 0.0)
        try:
            # если пришло строкой или иным типом — пробуем привести
            self.popularity_score = float(self.popularity_score)  # type: ignore[arg-type]
        except Exception:
            self.popularity_score = 0.0
        return self

    @field_validator("quest_data", mode="before")
    @classmethod
    def _parse_quest_data(cls, v: Any) -> dict[str, Any] | None:  # noqa: ANN001
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            import json

            try:
                parsed = json.loads(v)
            except Exception:
                return None
            return parsed if isinstance(parsed, dict) else None
        return None


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
