from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RelevanceWeights(BaseModel):
    title: float = 3.0
    body: float = 1.0
    tags: float = 1.5
    author: float = 0.5


class RelevanceBoosts(BaseModel):
    freshness: dict = Field(default_factory=lambda: {"half_life_days": 14})
    popularity: dict = Field(default_factory=lambda: {"weight": 1.0})


class RelevanceQueryParams(BaseModel):
    fuzziness: str = "AUTO"
    min_should_match: str = "2<75%"
    phrase_slop: int = 0
    tie_breaker: float | None = None


class RelevancePayload(BaseModel):
    weights: RelevanceWeights = Field(default_factory=RelevanceWeights)
    boosts: RelevanceBoosts = Field(default_factory=RelevanceBoosts)
    query: RelevanceQueryParams = Field(default_factory=RelevanceQueryParams)


class RelevanceGetOut(BaseModel):
    version: int
    payload: RelevancePayload
    updated_at: datetime


class DryRunDiffItem(BaseModel):
    query: str
    topBefore: list[str] = Field(default_factory=list)
    topAfter: list[str] = Field(default_factory=list)
    moved: list[dict[str, int]] = Field(default_factory=list)


class RelevancePutIn(BaseModel):
    payload: RelevancePayload
    dryRun: bool = False
    sample: list[str] = Field(default_factory=list)
    comment: str | None = None


class RelevanceApplyOut(BaseModel):
    version: int
    payload: RelevancePayload
    updated_at: datetime


class RelevanceDryRunOut(BaseModel):
    diff: list[DryRunDiffItem]
    warnings: list[str] = Field(default_factory=list)

