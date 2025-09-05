from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True)
class NodeEventBase:
    node_id: int
    slug: str
    author_id: UUID
    workspace_id: UUID | None = None
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True)
class NodeCreated(NodeEventBase):
    pass


@dataclass(frozen=True)
class NodeUpdated(NodeEventBase):
    tags_changed: bool = False


@dataclass(frozen=True)
class NodePublished(NodeEventBase):
    pass


@dataclass(frozen=True)
class NodeArchived(NodeEventBase):
    pass


@dataclass(frozen=True)
class AchievementUnlocked:
    achievement_id: UUID
    user_id: UUID
    workspace_id: UUID
    title: str
    message: str
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True)
class PurchaseCompleted:
    user_id: UUID
    workspace_id: UUID | None
    title: str
    message: str
    id: str = field(default_factory=lambda: uuid4().hex)


EVENT_METRIC_NAMES: dict[type, str] = {
    NodeCreated: "node.created",
    NodeUpdated: "node.updated",
    NodePublished: "node.publish",
    NodeArchived: "node.archived",
    AchievementUnlocked: "achievement",
    PurchaseCompleted: "purchase.completed",
}


__all__ = [
    "NodeEventBase",
    "NodeCreated",
    "NodeUpdated",
    "NodePublished",
    "NodeArchived",
    "AchievementUnlocked",
    "PurchaseCompleted",
    "EVENT_METRIC_NAMES",
]
