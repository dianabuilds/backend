from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModerationCaseFilters:
    page: int = 1
    size: int = 20
    statuses: tuple[str, ...] | None = None
    types: tuple[str, ...] | None = None
    queues: tuple[str, ...] | None = None
    assignees: tuple[str, ...] | None = None
    query: str | None = None

    def normalized(self) -> ModerationCaseFilters:
        return ModerationCaseFilters(
            page=max(1, int(self.page or 1)),
            size=max(1, int(self.size or 1)),
            statuses=self._normalize_tuple(self.statuses),
            types=self._normalize_tuple(self.types),
            queues=self._normalize_tuple(self.queues),
            assignees=self._normalize_tuple(self.assignees),
            query=(self.query or "").strip() or None,
        )

    @staticmethod
    def _normalize_tuple(values: Sequence[str] | None) -> tuple[str, ...] | None:
        if not values:
            return None
        normalized = tuple({str(v).strip() for v in values if str(v).strip()})
        return normalized or None


@dataclass(frozen=True)
class ModerationCaseCreateCommand:
    title: str
    description: str | None = None
    type: str = "general"
    status: str = "open"
    queue: str | None = None
    priority: str | None = None
    severity: str | None = None
    subject_id: str | None = None
    subject_type: str | None = None
    subject_label: str | None = None
    assignee_id: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    author_id: str | None = None

    def to_repo_payload(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "type": self.type or "general",
            "status": self.status or "open",
            "queue": self.queue,
            "priority": self.priority,
            "severity": self.severity,
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "subject_label": self.subject_label,
            "assignee_id": self.assignee_id,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ModerationCaseUpdateCommand:
    case_id: str
    actor_id: str | None = None
    title: str | None = None
    description: str | None = None
    status: str | None = None
    queue: str | None = None
    priority: str | None = None
    severity: str | None = None
    assignee_id: str | None = None
    tags: tuple[str, ...] | None = None
    metadata: Mapping[str, Any] | None = None

    def to_repo_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.title is not None:
            payload["title"] = self.title
        if self.description is not None:
            payload["description"] = self.description
        if self.status is not None:
            payload["status"] = self.status
        if self.queue is not None:
            payload["queue"] = self.queue
        if self.priority is not None:
            payload["priority"] = self.priority
        if self.severity is not None:
            payload["severity"] = self.severity
        if self.assignee_id is not None:
            payload["assignee_id"] = self.assignee_id
        if self.tags is not None:
            payload["tags"] = list(self.tags)
        if self.metadata is not None:
            payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True)
class ModerationCaseNoteCommand:
    case_id: str
    text: str
    author_id: str | None = None
    pinned: bool | None = None
    visibility: str | None = None

    def to_repo_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"text": self.text}
        if self.pinned is not None:
            payload["pinned"] = bool(self.pinned)
        if self.visibility is not None:
            payload["visibility"] = self.visibility
        return payload


__all__ = [
    "ModerationCaseFilters",
    "ModerationCaseCreateCommand",
    "ModerationCaseUpdateCommand",
    "ModerationCaseNoteCommand",
]
