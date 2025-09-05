from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from pydantic.alias_generators import to_camel


class NodeBase(BaseModel):
    """Base node payload shared by create and update schemas."""

    title: str | None = None
    is_visible: bool = Field(default=True, alias="isVisible")
    meta: dict = Field(default_factory=dict)
    premium_only: bool | None = Field(
        default=None,
        alias="premiumOnly",
        validation_alias=AliasChoices("premium_only", "is_premium_only", "premiumOnly"),
    )
    nft_required: str | None = Field(default=None, alias="nftRequired")
    ai_generated: bool | None = Field(default=None, alias="aiGenerated")
    allow_feedback: bool = Field(
        default=True,
        alias="allowFeedback",
        validation_alias=AliasChoices("allow_feedback", "allow_comments", "allowFeedback"),
    )
    is_recommendable: bool = Field(default=True, alias="isRecommendable")

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

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
            except Exception as err:
                _ = err
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}


class NodeCreate(NodeBase):
    slug: str | None = None


class NodeUpdate(BaseModel):
    slug: str | None = None
    title: str | None = None
    is_visible: bool | None = Field(
        default=None,
        alias="isVisible",
        validation_alias=AliasChoices("hidden", "is_visible", "isVisible"),
    )
    allow_feedback: bool | None = Field(
        default=None,
        alias="allowFeedback",
        validation_alias=AliasChoices("allow_feedback", "allow_comments", "allowFeedback"),
    )
    is_recommendable: bool | None = Field(default=None, alias="isRecommendable")
    premium_only: bool | None = Field(
        default=None,
        alias="premiumOnly",
        validation_alias=AliasChoices("premium_only", "is_premium_only", "premiumOnly"),
    )
    nft_required: str | None = Field(default=None, alias="nftRequired")
    ai_generated: bool | None = Field(default=None, alias="aiGenerated")

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def _reject_legacy_fields(cls, data: Any) -> Any:  # noqa: ANN101
        camel = "media" + "Urls"
        snake = "media_" + "urls"
        forbidden = {
            camel: "media",
            snake: "media",
            "tagSlugs": "tags",
            "tag_slugs": "tags",
            "nodes": "content",
        }
        if isinstance(data, dict):
            for field, replacement in forbidden.items():
                if field in data:
                    raise ValueError(f"'{field}' field is deprecated; use '{replacement}'")
        return data


class NodeOut(NodeBase):
    id: int
    slug: str
    author_id: UUID = Field(alias="authorId")
    created_by_user_id: UUID | None = Field(default=None, alias="createdByUserId")
    updated_by_user_id: UUID | None = Field(default=None, alias="updatedByUserId")
    views: int
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    popularity_score: float = Field(alias="popularityScore")
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    @field_validator("tags", mode="before")
    @classmethod
    def _parse_tags(cls, v: Any) -> list[str]:  # noqa: ANN001
        if v is None:
            return []
        if isinstance(v, list):
            if v and isinstance(v[0], str):
                return v
            return [getattr(t, "slug", str(t)) for t in v]
        return []

    @model_validator(mode="after")
    def _normalize_output(self) -> NodeOut:
        # Приводим popularity_score к числу (некорректные значения -> 0.0)
        try:
            self.popularity_score = float(self.popularity_score)  # type: ignore[arg-type]
        except Exception as err:
            _ = err
            self.popularity_score = 0.0
        return self


class NodeBulkOperation(BaseModel):
    """Payload for bulk node admin operations."""

    ids: list[int]
    op: Literal[
        "hide",
        "show",
        "toggle_premium",
        "toggle_recommendable",
    ]

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class NodeBulkPatchChanges(BaseModel):
    """Changes to apply in bulk operations."""

    is_visible: bool | None = Field(default=None, alias="isVisible")
    is_public: bool | None = Field(
        default=None,
        alias="isPublic",
        validation_alias=AliasChoices("is_public", "isPublic"),
    )
    premium_only: bool | None = Field(
        default=None,
        alias="premiumOnly",
        validation_alias=AliasChoices("premium_only", "is_premium_only", "premiumOnly"),
    )
    is_recommendable: bool | None = Field(default=None, alias="isRecommendable")
    workspace_id: UUID | None = Field(default=None, alias="workspaceId")
    delete: bool | None = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class NodeBulkPatch(BaseModel):
    """Payload for bulk node patch operations."""

    ids: list[int]
    changes: NodeBulkPatchChanges

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
