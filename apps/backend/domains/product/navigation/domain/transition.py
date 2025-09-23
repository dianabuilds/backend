from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class TransitionContext:
    session_id: str
    tenant_id: str
    user_id: str | None
    origin_node_id: int | None
    route_window: tuple[int, ...]
    limit_state: str
    premium_level: str
    mode: str
    requested_ui_slots: int
    policies_hash: str | None
    cache_seed: str
    created_at: datetime


@dataclass(frozen=True)
class TransitionCandidate:
    node_id: int
    provider: str
    score: float
    probability: float
    factors: Mapping[str, float]
    badge: str
    explain: str


@dataclass(frozen=True)
class TransitionDecision:
    context: TransitionContext
    candidates: tuple[TransitionCandidate, ...]
    selected_node_id: int | None
    ui_slots_granted: int
    limit_state: str
    mode: str
    pool_size: int
    temperature: float
    epsilon: float
    empty_pool: bool
    empty_pool_reason: str | None = None
    curated_blocked_reason: str | None = None
    served_from_cache: bool = False
    emergency_used: bool = False
    telemetry: Mapping[str, float] = field(default_factory=dict)
