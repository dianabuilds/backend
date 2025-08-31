from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .version import QuestVersionOut


class QuestStep(BaseModel):
    key: str
    title: str
    type: str = "normal"
    content: dict[str, Any] | None = None
    rewards: dict[str, Any] | None = None


class QuestTransition(BaseModel):
    from_node_key: str
    to_node_key: str
    label: str | None = None
    condition: dict[str, Any] | None = None


class QuestGraphIn(BaseModel):
    steps: list[QuestStep] = Field(default_factory=list)
    transitions: list[QuestTransition] = Field(default_factory=list)


class QuestGraphOut(BaseModel):
    version: QuestVersionOut
    steps: list[QuestStep] = Field(default_factory=list)
    transitions: list[QuestTransition] = Field(default_factory=list)
