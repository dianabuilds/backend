from __future__ import annotations

import hashlib
import logging
import math
import random
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

try:
    from prometheus_client import Counter  # type: ignore
except ImportError:  # pragma: no cover
    Counter = None  # type: ignore

from sqlalchemy.exc import SQLAlchemyError

from domains.product.navigation.application.ports import (
    NodesPort,
    TransitionRequest,
)
from domains.product.navigation.config import (
    DEFAULT_BADGES_BY_PROVIDER,
    DEFAULT_BASE_WEIGHTS,
    DEFAULT_MODE_CONFIGS,
    ModeConfig,
)
from domains.product.navigation.domain.transition import (
    TransitionCandidate,
    TransitionContext,
    TransitionDecision,
)

try:
    from domains.platform.telemetry.application.transition_metrics_service import (
        transition_metrics,
    )
except ModuleNotFoundError:  # pragma: no cover - telemetry optional in some tools
    transition_metrics = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NodeSnapshot:
    id: int
    author_id: str
    title: str | None
    tags: tuple[str, ...]
    is_public: bool
    embedding: tuple[float, ...] | None = None


BASE_WEIGHTS: dict[str, float] = DEFAULT_BASE_WEIGHTS.copy()
BADGES_BY_PROVIDER: dict[str, str] = DEFAULT_BADGES_BY_PROVIDER.copy()
MODE_CONFIGS: dict[str, ModeConfig] = DEFAULT_MODE_CONFIGS.copy()

UI_SLOTS: dict[str, dict[str, int]] = {
    "normal": {"free": 3, "premium": 3, "premium+": 4},
    "echo_boost": {"free": 3, "premium": 3, "premium+": 4},
    "discover": {"free": 3, "premium": 3, "premium+": 4},
    "editorial": {"free": 3, "premium": 3, "premium+": 4},
    "near_limit": {"free": 3, "premium": 3, "premium+": 4},
    "lite": {"free": 2, "premium": 2, "premium+": 2},
}

if Counter is not None:
    NAV_EMBEDDING_QUERIES = Counter(
        "navigation_embedding_queries_total",
        "Embedding retrieval usage in navigation",
        labelnames=("status",),
    )
else:
    NAV_EMBEDDING_QUERIES = None

ALLOWED_REASON_KEYS = {
    "curated",
    "tag_sim",
    "echo",
    "fresh",
    "diversity_bonus",
    "policy_penalty",
}


class NavigationService:
    def __init__(self, nodes: NodesPort):
        self.nodes = nodes

    def _record_embedding_usage(self, status: str) -> None:
        if NAV_EMBEDDING_QUERIES is None:
            return
        try:
            NAV_EMBEDDING_QUERIES.labels(status=status).inc()
        except (RuntimeError, ValueError) as exc:
            logger.debug(
                "nav_embedding_metric_failed", extra={"status": status}, exc_info=exc
            )

    def next(self, data: TransitionRequest) -> TransitionDecision:
        context = self._build_context(data)
        start = time.perf_counter()
        base_nodes, origin_node, route_nodes = self._prepare_universe(context)
        config = MODE_CONFIGS[context.mode]

        diversity_strength = 1.0
        k_limit = config.k_base
        random_enabled = config.allow_random
        relaxation_step = 0
        curated_blocked_reason: str | None = None
        rng = self._seeded_rng(context.cache_seed)
        pool_size = 0
        candidates: Sequence[TransitionCandidate] = ()
        empty_pool = False
        empty_pool_reason: str | None = None

        while relaxation_step < 4:
            seeds, curated_blocked = self._build_candidates(
                context=context,
                origin_node=origin_node,
                route_nodes=route_nodes,
                nodes=base_nodes,
                k_limit=k_limit,
                random_enabled=random_enabled,
                rng=rng,
            )
            curated_blocked_reason = curated_blocked_reason or curated_blocked
            scored = self._score_candidates(
                context=context,
                seeds=seeds,
                origin_node=origin_node,
                route_nodes=route_nodes,
                diversity_strength=diversity_strength,
                config=config,
            )
            pool_size = len(scored)
            if scored:
                candidates = self._select_candidates(
                    context=context,
                    scored=scored,
                    config=config,
                )
                if candidates:
                    break
            # relax per ladder
            relaxation_step += 1
            if relaxation_step == 1:
                diversity_strength = max(0.0, diversity_strength - 0.5)
            elif relaxation_step == 2:
                k_limit = int(math.ceil(k_limit * 1.25))
            elif relaxation_step == 3:
                if context.mode != "lite":
                    random_enabled = True
                    logger.info(
                        "nav_relaxation_enable_random",
                        extra={
                            "mode": context.mode,
                            "limit_state": context.limit_state,
                            "relaxation_step": relaxation_step,
                        },
                    )
                else:
                    # Lite mode disallows random; mark for final fallback
                    random_enabled = False
                    logger.info(
                        "nav_relaxation_random_blocked",
                        extra={
                            "mode": context.mode,
                            "limit_state": context.limit_state,
                            "reason": "lite_mode",
                        },
                    )
            else:
                empty_pool = True
                empty_pool_reason = "relaxation_exhausted"
                candidates = ()

            if relaxation_step >= 4:
                empty_pool = True
                empty_pool_reason = empty_pool_reason or "no_candidates"
                break

        if curated_blocked_reason:
            logger.debug(
                "nav_curated_blocked",
                extra={
                    "mode": context.mode,
                    "limit_state": context.limit_state,
                    "reason": curated_blocked_reason,
                },
            )
        if empty_pool or not candidates:
            logger.warning(
                "nav_candidates_fallback",
                extra={
                    "mode": context.mode,
                    "limit_state": context.limit_state,
                    "pool_size": pool_size,
                    "relaxation_step": relaxation_step,
                    "empty_pool_reason": empty_pool_reason
                    or ("no_candidates" if not candidates else None),
                    "curated_blocked_reason": curated_blocked_reason,
                },
            )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        decision = TransitionDecision(
            context=context,
            candidates=tuple(candidates),
            selected_node_id=(candidates[0].node_id if candidates else None),
            ui_slots_granted=min(context.requested_ui_slots, len(candidates)),
            limit_state=context.limit_state,
            mode=context.mode,
            pool_size=pool_size,
            temperature=config.temperature,
            epsilon=config.epsilon,
            empty_pool=empty_pool or not candidates,
            empty_pool_reason=empty_pool_reason,
            curated_blocked_reason=curated_blocked_reason,
            served_from_cache=False,
            emergency_used=data.emergency,
            telemetry={"time_ms": elapsed_ms},
        )
        self._record_transition_metrics(decision, elapsed_ms)
        return decision

    def _record_transition_metrics(
        self, decision: TransitionDecision, elapsed_ms: float
    ) -> None:
        if transition_metrics is None:
            return
        mode = (
            decision.mode or decision.context.mode or "default"
        ).strip().lower() or "default"
        try:
            transition_metrics.observe_latency(mode, elapsed_ms)
            candidates = decision.candidates
            if candidates:
                entropy = self._candidate_entropy(candidates)
                transition_metrics.observe_entropy(mode, entropy)
                transition_metrics.observe_repeat_rate(
                    mode, self._repeat_rate(decision.context.route_window, candidates)
                )
                transition_metrics.observe_novelty_rate(
                    mode, self._novelty_rate(candidates)
                )
            if decision.empty_pool or decision.pool_size == 0:
                transition_metrics.inc_no_route(mode)
            if (
                decision.empty_pool
                or decision.curated_blocked_reason
                or decision.emergency_used
            ):
                transition_metrics.inc_fallback(mode)
        except Exception:  # pragma: no cover - metrics must not disrupt traffic
            logger.debug(
                "nav_transition_metrics_record_failed",
                extra={"mode": mode},
                exc_info=True,
            )

    @staticmethod
    def _repeat_rate(
        route_window: Sequence[int], candidates: Sequence[TransitionCandidate]
    ) -> float:
        if not candidates:
            return 0.0
        window: set[int] = set()
        for node_id in route_window:
            try:
                window.add(int(node_id))
            except (TypeError, ValueError):
                continue
        if not window:
            return 0.0
        repeats = sum(1 for candidate in candidates if candidate.node_id in window)
        return repeats / len(candidates)

    @staticmethod
    def _novelty_rate(candidates: Sequence[TransitionCandidate]) -> float:
        if not candidates:
            return 0.0
        novel = 0
        for candidate in candidates:
            factors = candidate.factors or {}
            try:
                diversity_bonus = float(factors.get("diversity_bonus", 0.0))
            except (TypeError, ValueError):
                diversity_bonus = 0.0
            if (
                candidate.badge == "explore"
                or candidate.provider == "random"
                or diversity_bonus > 0.0
            ):
                novel += 1
        return novel / len(candidates)

    @staticmethod
    def _candidate_entropy(candidates: Sequence[TransitionCandidate]) -> float:
        if not candidates:
            return 0.0
        probs = []
        for candidate in candidates:
            try:
                value = float(candidate.probability)
            except (TypeError, ValueError):
                value = 0.0
            if value > 0.0:
                probs.append(value)
        if not probs:
            uniform = 1.0 / len(candidates)
            return -(uniform * math.log(uniform, 2)) * len(candidates)
        total = sum(probs)
        if total <= 0.0:
            uniform = 1.0 / len(candidates)
            return -(uniform * math.log(uniform, 2)) * len(candidates)
        entropy = 0.0
        for prob in probs:
            frac = prob / total
            if frac <= 0.0:
                continue
            entropy -= frac * math.log(frac, 2)
        return entropy

    def _build_context(self, data: TransitionRequest) -> TransitionContext:
        limit_state = data.limit_state or "normal"
        mode = (data.mode or "normal").lower()
        if limit_state == "exceeded_lite":
            mode = "lite"
        mode = mode if mode in MODE_CONFIGS else "normal"
        limit_state = (
            limit_state
            if limit_state in {"normal", "near_limit", "exceeded_lite"}
            else "normal"
        )
        premium = self._normalize_premium(data.premium_level)
        slots_map = UI_SLOTS.get(mode, UI_SLOTS["normal"])
        allowed = slots_map.get(premium, slots_map.get("free", 3))
        requested = data.requested_ui_slots if data.requested_ui_slots > 0 else allowed
        ui_slots = max(1, min(requested, allowed))
        cache_seed = self._compute_seed(
            user_id=data.user_id,
            session_id=data.session_id,
            origin_node_id=data.origin_node_id,
            limit_state=limit_state,
            mode=mode,
        )
        return TransitionContext(
            session_id=data.session_id,
            user_id=data.user_id,
            origin_node_id=data.origin_node_id,
            route_window=tuple(int(n) for n in data.route_window),
            limit_state=limit_state,
            premium_level=premium,
            mode=mode,
            requested_ui_slots=ui_slots,
            policies_hash=data.policies_hash,
            cache_seed=cache_seed,
            created_at=datetime.now(tz=UTC),
        )

    def _prepare_universe(
        self, context: TransitionContext
    ) -> tuple[list[NodeSnapshot], NodeSnapshot | None, list[NodeSnapshot]]:
        origin_node = self._fetch_node(context.origin_node_id)
        route_nodes: list[NodeSnapshot] = []
        seen_route: set[int] = set()
        for node_id in context.route_window:
            if node_id in seen_route:
                continue
            seen_route.add(node_id)
            snap = self._fetch_node(node_id)
            if snap is not None:
                route_nodes.append(snap)
        # Candidate universe: authors from origin, route, and user (treated as author)
        author_ids: set[str] = set()
        if origin_node is not None:
            author_ids.add(origin_node.author_id)
        for snap in route_nodes:
            author_ids.add(snap.author_id)
        if context.user_id:
            author_ids.add(context.user_id)
        nodes: dict[int, NodeSnapshot] = {}
        for author in author_ids:
            samples = self.nodes.list_by_author(author, limit=200)
            for item in samples:
                snap = self._normalize_node(item)
                if snap is None or not snap.is_public:
                    continue
                nodes.setdefault(snap.id, snap)
        # Remove origin from baseline to avoid duplication (curated step re-adds if needed)
        if origin_node is not None and origin_node.id in nodes:
            nodes.pop(origin_node.id, None)
        return list(nodes.values()), origin_node, route_nodes

    def _build_candidates(
        self,
        context: TransitionContext,
        origin_node: NodeSnapshot | None,
        route_nodes: Sequence[NodeSnapshot],
        nodes: Sequence[NodeSnapshot],
        k_limit: int,
        random_enabled: bool,
        rng: random.Random,
    ) -> tuple[list[dict], str | None]:
        seeds: list[dict] = []
        curated_blocked_reason: str | None = None
        route_author_ids = [snap.author_id for snap in route_nodes]
        recent_authors = route_author_ids[-3:]
        target_tags = self._aggregate_tags(origin_node, route_nodes)
        query_embedding = self._compose_query_embedding(
            origin_node, route_nodes, context
        )

        nodes_by_id: dict[int, NodeSnapshot] = {snap.id: snap for snap in nodes}
        ann_nodes: list[NodeSnapshot] = []
        embedding_status = "query_missing"
        ann_raw: list[dict[str, Any]] = []
        if query_embedding is not None:
            try:
                ann_raw = list(
                    self.nodes.search_by_embedding(
                        list(query_embedding), limit=max(k_limit * 2, 64)
                    )
                )
                embedding_status = "used" if ann_raw else "empty"
            except (
                SQLAlchemyError,
                RuntimeError,
                ValueError,
                TypeError,
                TimeoutError,
            ) as exc:
                logger.warning(
                    "nav_embedding_search_failed",
                    extra={
                        "source": "embedding",
                        "mode": context.mode,
                        "limit_state": context.limit_state,
                    },
                    exc_info=exc,
                )
                ann_raw = []
                embedding_status = "error"
            for item in ann_raw:
                snap = self._normalize_node(item)
                if snap is None or not snap.is_public:
                    continue
                if snap.id not in nodes_by_id:
                    nodes_by_id[snap.id] = snap
                    ann_nodes.append(snap)
        self._record_embedding_usage(embedding_status)

        def calc_similarity(snapshot: NodeSnapshot) -> float:
            sim = self._embedding_similarity(query_embedding, snapshot.embedding)
            if sim == 0.0:
                return self._tag_similarity(target_tags, snapshot.tags)
            return sim

        # Curated candidate: next node by origin author if available
        if origin_node is not None:
            same_author = [
                snap for snap in nodes if snap.author_id == origin_node.author_id
            ]
            same_author_sorted = sorted(same_author, key=lambda s: s.id)
            curated_candidate = None
            for snap in same_author_sorted:
                if snap.id != origin_node.id and snap.id not in context.route_window:
                    curated_candidate = snap
                    break
            if curated_candidate is not None:
                seeds.append(
                    {
                        "node": curated_candidate,
                        "provider": "curated",
                        "tag_sim": calc_similarity(curated_candidate),
                        "echo": 0.0,
                        "fresh_rank": curated_candidate.id,
                    }
                )
            else:
                curated_blocked_reason = "no_curated_candidate"
        # Score non-curated candidates
        combined_nodes = list(nodes_by_id.values())
        combined_nodes.extend(ann_nodes)
        ranked = sorted(
            combined_nodes,
            key=lambda snap: (calc_similarity(snap), snap.id),
            reverse=True,
        )
        trimmed = ranked[: max(k_limit, len(seeds))]
        used_ids = {seed["node"].id for seed in seeds}
        for snap in trimmed:
            if snap.id in used_ids:
                continue
            provider = "compass"
            echo_score = 0.0
            if snap.author_id in recent_authors:
                provider = "echo"
                echo_score = 1.0
            seeds.append(
                {
                    "node": snap,
                    "provider": provider,
                    "tag_sim": self._tag_similarity(target_tags, snap.tags),
                    "echo": echo_score,
                    "fresh_rank": snap.id,
                }
            )
            used_ids.add(snap.id)
        if random_enabled:
            pool_ids = {seed["node"].id for seed in seeds}
            remaining = [snap for snap in combined_nodes if snap.id not in pool_ids]
            rng.shuffle(remaining)
            for snap in remaining[: max(0, k_limit - len(seeds))]:
                seeds.append(
                    {
                        "node": snap,
                        "provider": "random",
                        "tag_sim": calc_similarity(snap),
                        "echo": 0.0,
                        "fresh_rank": snap.id,
                    }
                )
        return seeds, curated_blocked_reason

    def _score_candidates(
        self,
        context: TransitionContext,
        seeds: Iterable[dict],
        origin_node: NodeSnapshot | None,
        route_nodes: Sequence[NodeSnapshot],
        diversity_strength: float,
        config: ModeConfig,
    ) -> list[dict]:
        if origin_node is None and not route_nodes and not seeds:
            return []
        route_author_ids = [snap.author_id for snap in route_nodes]
        last_author = route_author_ids[-1] if route_author_ids else None
        results: list[dict] = []
        if not seeds:
            return results
        max_rank = max(seed["fresh_rank"] for seed in seeds)
        for seed in seeds:
            node: NodeSnapshot = seed["node"]
            if node.id in context.route_window:
                continue
            factors = {
                "curated": 1.0 if seed["provider"] == "curated" else 0.0,
                "tag_sim": float(seed.get("tag_sim") or 0.0),
                "echo": float(seed.get("echo") or 0.0),
                "fresh": 1.0 - ((max_rank - seed["fresh_rank"]) / max(1, max_rank)),
                "diversity_bonus": (
                    1.0 if node.author_id not in route_author_ids else 0.0
                ),
                "policy_penalty": 0.0,
            }
            penalty = 0.0
            if (
                diversity_strength > 0
                and last_author is not None
                and node.author_id == last_author
                and len(route_author_ids) >= config.author_threshold
            ):
                penalty = diversity_strength * 0.5
            score = sum(BASE_WEIGHTS[k] * factors.get(k, 0.0) for k in BASE_WEIGHTS)
            if seed["provider"] == "curated":
                score += config.curated_boost
            score -= penalty
            results.append(
                {
                    "node": node,
                    "provider": seed["provider"],
                    "score": score,
                    "factors": {
                        k: factors[k] for k in ALLOWED_REASON_KEYS if k in factors
                    },
                }
            )
        results.sort(key=lambda item: item["score"], reverse=True)
        return results

    def _select_candidates(
        self,
        context: TransitionContext,
        scored: Sequence[dict],
        config: ModeConfig,
    ) -> list[TransitionCandidate]:
        if not scored:
            return []
        t = max(config.temperature, 1e-6)
        scores = [item["score"] for item in scored]
        max_score = max(scores)
        exp_values = [math.exp((score - max_score) / t) for score in scores]
        total = sum(exp_values) or 1.0
        probabilities = [val / total for val in exp_values]
        ranked = list(zip(scored, probabilities, strict=False))
        ranked.sort(key=lambda pair: pair[1], reverse=True)
        limit = min(context.requested_ui_slots, len(ranked))
        results: list[TransitionCandidate] = []
        for item, prob in ranked[:limit]:
            node: NodeSnapshot = item["node"]
            provider = item["provider"]
            badge = BADGES_BY_PROVIDER.get(provider, "similar")
            if context.mode == "lite":
                badge = "limited"
            explain = self._explain(provider)
            factors = dict(item["factors"].items())
            # Ensure allowed keys only
            for key in list(factors.keys()):
                if key not in ALLOWED_REASON_KEYS:
                    factors.pop(key)
            results.append(
                TransitionCandidate(
                    node_id=node.id,
                    provider=provider,
                    score=item["score"],
                    probability=prob,
                    factors=factors,
                    badge=badge,
                    explain=explain,
                )
            )
        return results

    def _fetch_node(self, node_id: int | None) -> NodeSnapshot | None:
        if node_id is None:
            return None
        raw = self.nodes.get(int(node_id))
        return self._normalize_node(raw)

    def _normalize_node(self, raw: dict[str, Any] | None) -> NodeSnapshot | None:
        if not raw:
            return None
        raw_id = raw.get("id")
        if raw_id is None:
            return None
        try:
            node_id = int(cast(int | float | str, raw_id))
        except (TypeError, ValueError):
            return None
        author = str(raw.get("author_id") or "")
        if not author:
            return None
        title_raw = raw.get("title")
        title = str(title_raw) if isinstance(title_raw, str) else None
        tags_field = raw.get("tags")
        tags: tuple[str, ...]
        if isinstance(tags_field, (list, tuple)):
            tags = tuple(str(t).lower() for t in tags_field if isinstance(t, str))
        else:
            tags = ()
        embedding_field = raw.get("embedding")
        embedding: tuple[float, ...] | None = None
        if isinstance(embedding_field, (list, tuple)):
            try:
                embedding = tuple(float(v) for v in embedding_field)
            except (TypeError, ValueError) as exc:
                logger.debug(
                    "nav_embedding_parse_failed",
                    extra={"node_id": node_id},
                    exc_info=exc,
                )
                embedding = None
        is_public = bool(raw.get("is_public", True))
        return NodeSnapshot(
            id=node_id,
            author_id=author,
            title=title,
            tags=tags,
            is_public=is_public,
            embedding=embedding,
        )

    def _aggregate_tags(
        self, origin: NodeSnapshot | None, route_nodes: Sequence[NodeSnapshot]
    ) -> set[str]:
        tags: set[str] = set()
        if origin is not None:
            tags.update(origin.tags)
        for snap in route_nodes:
            tags.update(snap.tags)
        return tags

    def _compose_query_embedding(
        self,
        origin: NodeSnapshot | None,
        route_nodes: Sequence[NodeSnapshot],
        context: TransitionContext,
    ) -> tuple[float, ...] | None:
        vectors: list[tuple[float, ...]] = []
        weights: list[float] = []
        if origin is not None and origin.embedding is not None:
            norm = self._normalize_vector(origin.embedding)
            if norm is not None:
                vectors.append(tuple(norm))
                weights.append(0.6)
        history = [
            snap.embedding for snap in route_nodes[-3:] if snap.embedding is not None
        ]
        if history:
            mean_vec = self._mean_vector(history)
            norm_mean = self._normalize_vector(mean_vec)
            if norm_mean is not None:
                vectors.append(tuple(norm_mean))
                weights.append(0.2)
        if not vectors:
            return None
        size = len(vectors[0])
        combined = [0.0] * size
        total = sum(weights)
        for vec, weight in zip(vectors, weights, strict=False):
            if len(vec) != size:
                continue
            for idx, value in enumerate(vec):
                combined[idx] += weight * value
        if total <= 0:
            return None
        combined = [value / total for value in combined]
        normalized = self._normalize_vector(combined)
        if normalized is None:
            return None
        return tuple(normalized)

    @staticmethod
    def _mean_vector(vectors: Sequence[Sequence[float]]) -> list[float] | None:
        if not vectors:
            return None
        size = len(vectors[0])
        acc = [0.0] * size
        count = 0
        for vec in vectors:
            if len(vec) != size:
                continue
            for idx, value in enumerate(vec):
                acc[idx] += float(value)
            count += 1
        if count == 0:
            return None
        return [value / count for value in acc]

    @staticmethod
    def _normalize_vector(values: Sequence[float] | None) -> list[float] | None:
        if values is None:
            return None
        acc = [float(v) for v in values]
        norm = math.sqrt(sum(v * v for v in acc))
        if norm <= 0:
            return None
        return [v / norm for v in acc]

    @staticmethod
    def _embedding_similarity(
        query: Sequence[float] | None, candidate: Sequence[float] | None
    ) -> float:
        if query is None or candidate is None:
            return 0.0
        if len(query) != len(candidate):
            return 0.0
        score = sum(a * b for a, b in zip(query, candidate, strict=False))
        return max(-1.0, min(1.0, score))

    @staticmethod
    def _tag_similarity(target_tags: set[str], candidate_tags: Sequence[str]) -> float:
        if not target_tags or not candidate_tags:
            return 0.0
        cand = set(candidate_tags)
        inter = len(target_tags & cand)
        union = len(target_tags | cand)
        if union == 0:
            return 0.0
        return inter / union

    @staticmethod
    def _compute_seed(
        *,
        user_id: str,
        session_id: str,
        origin_node_id: int | None,
        limit_state: str,
        mode: str,
    ) -> str:
        payload = "|".join(
            [
                user_id,
                session_id,
                str(origin_node_id or 0),
                limit_state,
                mode,
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _seeded_rng(seed_hex: str) -> random.Random:
        seed_int = int(seed_hex[:16], 16)
        return random.Random(seed_int)

    @staticmethod
    def _normalize_premium(level: str | None) -> str:
        if not level:
            return "free"
        value = level.strip().lower()
        if value in {"premium+", "premium-plus", "premium_plus"}:
            return "premium+"
        if value == "premium":
            return "premium"
        return "free"

    @staticmethod
    def _explain(provider: str) -> str:
        if provider == "curated":
            return "Next trail step"
        if provider == "echo":
            return "Similar topic seen earlier"
        if provider == "random":
            return "New branch for diversity"
        return "Similar topic"
