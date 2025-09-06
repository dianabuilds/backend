from __future__ import annotations

import copy
import logging
import math
import time
from collections import Counter, defaultdict, deque
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.preview import PreviewContext  # isort: skip
from app.core.log_events import no_route, transition_finish, transition_start
from app.core.transition_metrics import (
    record_fallback_used,
    record_no_route,
    record_novelty_rate,
    record_repeat_rate,
    record_route_latency_ms,
    record_route_length,
    record_tag_entropy,
)
from app.domains.telemetry.application.transition_metrics_facade import (
    transition_metrics,
)

from .policies import Policy

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from app.domains.nodes.infrastructure.models.node import Node
    from app.domains.users.infrastructure.models.user import User

logger = logging.getLogger(__name__)


def _compute_entropy(tags: Sequence[str]) -> float:
    if not tags:
        return 0.0
    counts = Counter(tags)
    total = sum(counts.values())
    return -sum((c / total) * math.log(c / total) for c in counts.values())


class RepeatFilter:
    """Filter penalizing repeated tags and sources and limiting node visits."""

    def __init__(
        self,
        window: int,
        threshold: float,
        decay: float,
        max_visits: int,
    ) -> None:
        self.window = window
        self.threshold = threshold
        self.decay = decay
        self.max_visits = max_visits
        self.tag_history: deque[str] = deque()
        self.source_history: deque[str] = deque()
        self.tag_counts: dict[str, int] = defaultdict(int)
        self.source_counts: dict[str, int] = defaultdict(int)
        self.visit_counts: dict[str, int] = defaultdict(int)

    def _add(self, history: deque[str], counts: dict[str, int], value: str) -> None:
        history.append(value)
        counts[value] += 1
        if self.window and len(history) > self.window:
            old = history.popleft()
            counts[old] -= 1
            if counts[old] <= 0:
                del counts[old]

    def update(self, node: Node) -> None:
        self.visit_counts[node.slug] += 1
        for tag in getattr(node, "tags", []) or []:
            self._add(self.tag_history, self.tag_counts, tag)
        source = getattr(node, "source", None)
        if source:
            self._add(self.source_history, self.source_counts, source)

    def _score(self, node: Node) -> float:
        scores: list[float] = []
        for tag in getattr(node, "tags", []) or []:
            count = self.tag_counts.get(tag, 0)
            scores.append(self.decay**count)
        source = getattr(node, "source", None)
        if source:
            count = self.source_counts.get(source, 0)
            scores.append(self.decay**count)
        return min(scores) if scores else 1.0

    def filter(self, nodes: Sequence[Node]) -> tuple[list[Node], list[str]]:
        allowed: list[Node] = []
        filtered: list[str] = []
        for n in nodes:
            if self.max_visits and self.visit_counts.get(n.slug, 0) >= self.max_visits:
                filtered.append(n.slug)
                continue
            if self.window > 0:
                score = self._score(n)
                if score < self.threshold:
                    filtered.append(n.slug)
                    continue
            allowed.append(n)
        return allowed, filtered


@dataclass
class TransitionTrace:
    candidates: list[str]
    filtered: list[str]
    selected: str | None
    reason: str | None = None
    policy: str | None = None


class NoRouteReason(Enum):
    NO_ROUTE = "NO_ROUTE"
    TIMEOUT = "timeout"
    BUDGET_EXCEEDED = "budget_exceeded"


@dataclass
class TransitionResult:
    next: Node | None
    reason: NoRouteReason | None
    trace: list[TransitionTrace]
    metrics: dict


class TransitionRouter:
    """Routes transitions according to provided policies."""

    def __init__(
        self,
        policies: Sequence[Policy],
        not_repeat_last: int = 0,
        no_repeat_window: int = 0,
        repeat_threshold: float = 0.0,
        repeat_decay: float = 1.0,
        max_visits: int = 0,
    ) -> None:
        self.policies = list(policies)
        self.policy_map = {p.name: p for p in self.policies}
        self.history: deque[str] = deque(maxlen=not_repeat_last)
        self.trace: list[TransitionTrace] = []
        self.repeat_filter = RepeatFilter(
            no_repeat_window, repeat_threshold, repeat_decay, max_visits
        )

    async def route(
        self,
        db: AsyncSession,
        start: Node,
        user: User | None,
        budget,
        mode: str | None = None,
        preview: PreviewContext | None = None,
    ) -> TransitionResult:
        transition_start(start.slug)
        start_time = time.monotonic()
        self.trace.clear()
        seed = preview.seed if preview else None
        if seed is not None:
            for pol in self.policies:
                if hasattr(pol, "set_seed"):
                    pol.set_seed(seed)
                if hasattr(pol.provider, "set_seed"):
                    pol.provider.set_seed(seed)

        history = self.history
        repeat_filter = self.repeat_filter
        if preview and preview.mode != "off":
            history = deque(self.history, maxlen=self.history.maxlen)
            repeat_filter = copy.deepcopy(self.repeat_filter)

        history.append(start.slug)
        repeat_filter.update(start)

        policy: Policy | None = self.policy_map.get(mode) if mode else None
        if policy is not None:
            policy_order = [policy] + [p for p in self.policies if p.name != mode]
        elif getattr(budget, "fallback_chain", None):
            policy_order = [
                p
                for name in getattr(budget, "fallback_chain", [])
                if (p := self.policy_map.get(name))
            ]
        else:
            policy_order = list(self.policies)

        fallback_used = False
        queries = 0
        filtered_total = 0
        nxt: Node | None = None
        reason: NoRouteReason | None = None

        for idx, policy in enumerate(policy_order):
            candidate, trace = await policy.choose(db, start, user, history, repeat_filter, preview)
            trace.policy = policy.name
            self.trace.append(trace)
            queries += 1
            filtered_total += len(trace.filtered)

            elapsed_ms = (time.monotonic() - start_time) * 1000
            if elapsed_ms > getattr(budget, "max_time_ms", float("inf")):
                reason = NoRouteReason.TIMEOUT
                break
            if queries > getattr(budget, "max_queries", float("inf")) or filtered_total > getattr(
                budget, "max_filters", float("inf")
            ):
                reason = NoRouteReason.BUDGET_EXCEEDED
                break

            if candidate and candidate.slug not in history:
                if idx > 0:
                    fallback_used = True
                history.append(candidate.slug)
                repeat_filter.update(candidate)
                logger.debug("%s -> %s", policy.name, candidate.slug)
                nxt = candidate
                break

        elapsed_ms = (time.monotonic() - start_time) * 1000
        total_candidates = sum(len(t.candidates) for t in self.trace)
        repeat_rate = filtered_total / total_candidates if total_candidates else 0.0
        novelty_rate = 1.0 - repeat_rate
        metrics = {
            "elapsed_ms": elapsed_ms,
            "db_queries": queries,
            "repeat_rate": repeat_rate,
            "novelty_rate": novelty_rate,
            "fallback_used": fallback_used,
        }
        record_route_latency_ms(elapsed_ms)
        record_repeat_rate(repeat_rate)
        record_novelty_rate(novelty_rate)
        ws_id = str(start.workspace_id)
        metrics_mode = mode or (preview.mode if preview else "normal")
        transition_metrics.observe_latency(ws_id, metrics_mode, elapsed_ms)
        transition_metrics.observe_repeat_rate(ws_id, metrics_mode, repeat_rate)
        transition_metrics.observe_novelty_rate(ws_id, metrics_mode, novelty_rate)
        logger.info("navigation.novelty", extra={"novelty_rate": novelty_rate})
        if reason is None and nxt is None:
            reason = NoRouteReason.NO_ROUTE
            no_route(start.slug)
        if reason == NoRouteReason.NO_ROUTE:
            record_no_route(ws_id)
            transition_metrics.inc_no_route(ws_id, metrics_mode)
        else:
            record_route_length(len(history), ws_id)
            if nxt is not None:
                tags = getattr(nxt, "tags", []) or []
                ent = _compute_entropy([getattr(t, "slug", t) for t in tags])
                record_tag_entropy(ent, ws_id)
                transition_metrics.observe_entropy(ws_id, metrics_mode, ent)
        if fallback_used:
            from app.core.log_events import fallback_used as log_fallback_used

            log_fallback_used("transition.router")
            record_fallback_used(ws_id)
            transition_metrics.inc_fallback(ws_id, metrics_mode)
        transition_finish(nxt.slug if nxt else None)
        return TransitionResult(next=nxt, reason=reason, trace=list(self.trace), metrics=metrics)
