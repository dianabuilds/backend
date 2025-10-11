from __future__ import annotations

import hashlib
import logging
import math
import random
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

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

from .ports import NodesPort, TransitionRequest

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NodeSnapshot:
    id: int
    author_id: str | None
    title: str | None
    tags: tuple[str, ...]
    is_public: bool
    embedding: tuple[float, ...] | None


@dataclass
class _CandidateEnvelope:
    snapshot: NodeSnapshot
    provider: str
    score: float
    factors: dict[str, float]


class NavigationService:
    """Entry point for navigation recommendations."""

    def __init__(
        self,
        *,
        nodes: NodesPort,
        mode_configs: Mapping[str, ModeConfig] | None = None,
        base_weights: Mapping[str, float] | None = None,
        badges: Mapping[str, str] | None = None,
    ) -> None:
        self.nodes = nodes
        self._mode_configs = {
            key.lower(): cfg for key, cfg in DEFAULT_MODE_CONFIGS.items()
        }
        if mode_configs:
            for key, cfg in mode_configs.items():
                if isinstance(cfg, ModeConfig):
                    self._mode_configs[str(key).lower()] = cfg
        self._base_weights = dict(DEFAULT_BASE_WEIGHTS)
        if base_weights:
            for key, value in base_weights.items():
                try:
                    self._base_weights[str(key)] = float(value)
                except (TypeError, ValueError):
                    continue
        self._badges = dict(DEFAULT_BADGES_BY_PROVIDER)
        if badges:
            for key, badge_value in badges.items():
                self._badges[str(key)] = str(badge_value)
        self._default_mode = "normal"
        self._random = random.Random()
        self._search_multiplier = 2

    def next(self, request: TransitionRequest) -> TransitionDecision:
        mode_key = str(request.mode or self._default_mode).strip().lower()
        if not mode_key:
            mode_key = self._default_mode
        mode_config = self._resolve_mode_config(mode_key)
        provider_filter = self._normalize_provider_filter(
            request.requested_provider_overrides
        )
        providers = self._select_providers(mode_config, provider_filter)
        cache_seed = self._generate_cache_seed(request)
        context = self._build_context(
            request,
            cache_seed=cache_seed,
            mode_name=mode_config.name,
        )
        origin = self._load_node(request.origin_node_id)
        history = self._load_history(context.route_window)
        query_embedding = self._compose_query_embedding(origin, history, context)
        raw_candidates = self._gather_candidates(
            providers=providers,
            mode_config=mode_config,
            context=context,
            origin=origin,
            history=history,
            query_embedding=query_embedding,
        )
        candidates = self._finalize_candidates(
            raw_candidates, limit=max(1, mode_config.k_base)
        )
        pool_size = len(candidates)
        empty_pool = pool_size == 0
        selected_node_id = candidates[0].node_id if candidates else None
        ui_slots_granted = (
            min(context.requested_ui_slots, pool_size) if pool_size else 0
        )
        telemetry = self._build_telemetry(candidates, query_embedding=query_embedding)
        decision = TransitionDecision(
            context=context,
            candidates=tuple(candidates),
            selected_node_id=selected_node_id,
            ui_slots_granted=ui_slots_granted,
            limit_state=context.limit_state,
            mode=mode_config.name,
            pool_size=pool_size,
            temperature=mode_config.temperature,
            epsilon=mode_config.epsilon,
            empty_pool=empty_pool,
            empty_pool_reason="no_candidates" if empty_pool else None,
            curated_blocked_reason=None,
            served_from_cache=False,
            emergency_used=bool(request.emergency),
            telemetry=telemetry,
        )
        return decision

    def _generate_cache_seed(self, request: TransitionRequest) -> str:
        material = f"{request.session_id}:{request.user_id}:{datetime.now(UTC).timestamp()}:{self._random.random()}"
        digest = hashlib.sha1(material.encode("utf-8"), usedforsecurity=False)
        return digest.hexdigest()

    def _build_context(
        self,
        request: TransitionRequest,
        *,
        cache_seed: str,
        mode_name: str,
    ) -> TransitionContext:
        route_window = self._sanitize_route_window(request.route_window)
        requested_slots = request.requested_ui_slots
        if requested_slots is None or requested_slots <= 0:
            requested_slots = 3
        now = datetime.now(UTC)
        policies_hash = (
            str(request.policies_hash) if request.policies_hash is not None else None
        )
        return TransitionContext(
            session_id=str(request.session_id or ""),
            user_id=str(request.user_id or "") or None,
            origin_node_id=(
                int(request.origin_node_id)
                if request.origin_node_id is not None
                else None
            ),
            route_window=route_window,
            limit_state=str(request.limit_state or "normal"),
            premium_level=str(request.premium_level or "free"),
            mode=mode_name,
            requested_ui_slots=int(requested_slots),
            policies_hash=policies_hash,
            cache_seed=cache_seed,
            created_at=now,
        )

    def _sanitize_route_window(self, values: Sequence[int]) -> tuple[int, ...]:
        seen: set[int] = set()
        sanitized: list[int] = []
        for value in values:
            try:
                normalized = int(value)
            except (TypeError, ValueError):
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            sanitized.append(normalized)
        return tuple(sanitized)

    def _load_history(self, window: Sequence[int]) -> list[NodeSnapshot]:
        history: list[NodeSnapshot] = []
        for node_id in window:
            snapshot = self._load_node(node_id)
            if snapshot is not None:
                history.append(snapshot)
        return history

    def _load_node(self, node_id: int | None) -> NodeSnapshot | None:
        if node_id is None:
            return None
        try:
            raw = self.nodes.get(int(node_id))
        except Exception:  # pragma: no cover - defensive against integration issues
            logger.debug("navigation: failed to load node %s", node_id, exc_info=True)
            return None
        return self._to_snapshot(raw)

    def _to_snapshot(self, data: Any) -> NodeSnapshot | None:
        if data is None:
            return None
        if isinstance(data, NodeSnapshot):
            return data
        raw: Mapping[str, Any]
        if isinstance(data, Mapping):
            raw = cast(Mapping[str, Any], data)
        else:
            try:
                raw = cast(Mapping[str, Any], data.__dict__)
            except AttributeError:
                return None
        raw_id: Any = raw.get("id")
        if raw_id is None:
            return None
        try:
            node_id = int(raw_id)
        except (TypeError, ValueError):
            return None
        author = raw.get("author_id")
        author_id = str(author) if author not in (None, "") else None
        title = raw.get("title")
        title_str = str(title) if isinstance(title, str) else None
        tags_raw = raw.get("tags") or ()
        tags: tuple[str, ...]
        if isinstance(tags_raw, Sequence) and not isinstance(tags_raw, (str, bytes)):
            tags = tuple(
                str(tag).strip()
                for tag in tags_raw
                if isinstance(tag, str) and str(tag).strip()
            )
        else:
            tags = tuple()
        embedding_raw = raw.get("embedding")
        embedding: tuple[float, ...] | None = None
        if isinstance(embedding_raw, Sequence) and not isinstance(
            embedding_raw, (str, bytes)
        ):
            coords: list[float] = []
            for value in embedding_raw:
                try:
                    coords.append(float(value))
                except (TypeError, ValueError):
                    continue
            if coords:
                embedding = tuple(coords)
        is_public = bool(raw.get("is_public", False))
        return NodeSnapshot(
            id=node_id,
            author_id=author_id,
            title=title_str,
            tags=tags,
            is_public=is_public,
            embedding=embedding,
        )

    def _compose_query_embedding(
        self,
        origin: NodeSnapshot | None,
        history: Sequence[NodeSnapshot],
        context: TransitionContext,
    ) -> tuple[float, ...] | None:
        vectors: list[tuple[float, ...]] = []
        if origin and origin.embedding:
            vectors.append(origin.embedding)
        for item in history:
            if item.embedding:
                if vectors and len(item.embedding) != len(vectors[0]):
                    continue
                vectors.append(item.embedding)
        if not vectors:
            return None
        dimension = len(vectors[0])
        accumulator = [0.0] * dimension
        for vector in vectors:
            for idx, value in enumerate(vector):
                accumulator[idx] += value
        averaged = [value / len(vectors) for value in accumulator]
        return self._normalize_vector(averaged)

    def _normalize_vector(self, vector: Sequence[float]) -> tuple[float, ...]:
        norm = math.sqrt(sum(value * value for value in vector))
        if norm <= 0:
            return tuple(float(value) for value in vector)
        return tuple(float(value) / norm for value in vector)

    def _embedding_similarity(
        self, left: Sequence[float], right: Sequence[float]
    ) -> float:
        if not left or not right:
            return 0.0
        length = min(len(left), len(right))
        if length == 0:
            return 0.0
        dot = sum(float(left[i]) * float(right[i]) for i in range(length))
        norm_left = math.sqrt(sum(float(value) ** 2 for value in left[:length]))
        norm_right = math.sqrt(sum(float(value) ** 2 for value in right[:length]))
        denominator = norm_left * norm_right
        if denominator <= 0:
            return 0.0
        result = dot / denominator
        return max(min(result, 1.0), -1.0)

    def _normalize_provider_filter(
        self, overrides: Sequence[str] | None
    ) -> set[str] | None:
        if not overrides:
            return None
        normalized = {
            str(item).strip().lower() for item in overrides if str(item).strip()
        }
        return normalized or None

    def _resolve_mode_config(self, mode_key: str) -> ModeConfig:
        config = self._mode_configs.get(mode_key)
        if config is not None:
            return config
        default = self._mode_configs.get(self._default_mode)
        if default is not None:
            return default
        return next(iter(self._mode_configs.values()))

    def _select_providers(
        self,
        mode_config: ModeConfig,
        provider_filter: set[str] | None,
    ) -> tuple[str, ...]:
        providers = tuple(
            provider
            for provider in mode_config.providers
            if provider_filter is None or provider in provider_filter
        )
        if providers:
            return providers
        if provider_filter:
            return tuple(provider_filter)
        return mode_config.providers

    def _search_by_embedding(
        self, embedding: Sequence[float], *, limit: int
    ) -> Sequence[Any]:
        search = getattr(self.nodes, "search_by_embedding", None)
        if not callable(search):
            return []
        try:
            return search(list(float(value) for value in embedding), limit=limit)
        except Exception:  # pragma: no cover - defensive logging only
            logger.debug("navigation: embedding search failed", exc_info=True)
            return []

    def _list_by_author(
        self, author_id: str, *, limit: int, offset: int = 0
    ) -> list[NodeSnapshot]:
        try:
            records = self.nodes.list_by_author(
                author_id, limit=max(1, limit), offset=max(0, offset)
            )
        except Exception:  # pragma: no cover - defensive logging only
            logger.debug(
                "navigation: author listing failed for %s", author_id, exc_info=True
            )
            return []
        snapshots = [self._to_snapshot(item) for item in records]
        return [snap for snap in snapshots if snap is not None]

    def _snapshots_from_records(self, records: Iterable[Any]) -> list[NodeSnapshot]:
        snapshots: list[NodeSnapshot] = []
        for record in records:
            snapshot = self._to_snapshot(record)
            if snapshot is not None:
                snapshots.append(snapshot)
        return snapshots

    def _gather_candidates(
        self,
        *,
        providers: Sequence[str],
        mode_config: ModeConfig,
        context: TransitionContext,
        origin: NodeSnapshot | None,
        history: Sequence[NodeSnapshot],
        query_embedding: tuple[float, ...] | None,
    ) -> list[_CandidateEnvelope]:
        used_ids: set[int] = {snap.id for snap in history}
        if origin is not None:
            used_ids.add(origin.id)
        per_provider_limit = max(1, mode_config.k_base)
        collected: list[_CandidateEnvelope] = []
        for provider in providers:
            if provider == "compass":
                items = self._embedding_candidates(
                    query_embedding,
                    origin=origin,
                    used_ids=used_ids,
                    limit=per_provider_limit,
                )
            elif provider in {"echo", "curated"}:
                items = self._author_candidates(
                    context,
                    origin=origin,
                    used_ids=used_ids,
                    limit=per_provider_limit,
                )
            elif provider == "random":
                items = self._random_candidates(
                    context,
                    origin=origin,
                    history=history,
                    used_ids=used_ids,
                    limit=per_provider_limit,
                )
            else:
                items = self._author_candidates(
                    context,
                    origin=origin,
                    used_ids=used_ids,
                    limit=per_provider_limit,
                )
            for item in items:
                if item.snapshot.id in used_ids:
                    continue
                collected.append(item)
                used_ids.add(item.snapshot.id)
        if not collected and origin is not None:
            fallback = self._author_candidates(
                context,
                origin=origin,
                used_ids=used_ids,
                limit=mode_config.k_base,
            )
            for item in fallback:
                if item.snapshot.id in used_ids:
                    continue
                collected.append(item)
                used_ids.add(item.snapshot.id)
        return collected

    def _embedding_candidates(
        self,
        query_embedding: tuple[float, ...] | None,
        *,
        origin: NodeSnapshot | None,
        used_ids: set[int],
        limit: int,
    ) -> list[_CandidateEnvelope]:
        if query_embedding is None:
            return []
        records = self._search_by_embedding(
            query_embedding, limit=limit * self._search_multiplier
        )
        snapshots = self._snapshots_from_records(records)
        return self._score_snapshots(
            snapshots,
            provider="compass",
            origin=origin,
            query_embedding=query_embedding,
            used_ids=used_ids,
            limit=limit,
        )

    def _author_candidates(
        self,
        context: TransitionContext,
        *,
        origin: NodeSnapshot | None,
        used_ids: set[int],
        limit: int,
    ) -> list[_CandidateEnvelope]:
        author_id = None
        if origin and origin.author_id:
            author_id = origin.author_id
        elif context.user_id:
            author_id = context.user_id
        if not author_id:
            return []
        snapshots = self._list_by_author(
            author_id, limit=limit * self._search_multiplier
        )
        return self._score_snapshots(
            snapshots,
            provider="echo",
            origin=origin,
            query_embedding=None,
            used_ids=used_ids,
            limit=limit,
        )

    def _random_candidates(
        self,
        context: TransitionContext,
        *,
        origin: NodeSnapshot | None,
        history: Sequence[NodeSnapshot],
        used_ids: set[int],
        limit: int,
    ) -> list[_CandidateEnvelope]:
        pool: list[NodeSnapshot] = []
        author_id = origin.author_id if origin and origin.author_id else context.user_id
        if author_id:
            pool.extend(
                self._list_by_author(author_id, limit=limit * self._search_multiplier)
            )
        if not pool:
            pool.extend(history)
        deduplicated: list[NodeSnapshot] = []
        seen: set[int] = set()
        for item in pool:
            if item.id in seen or item.id in used_ids:
                continue
            seen.add(item.id)
            deduplicated.append(item)
        self._random.shuffle(deduplicated)
        return self._score_snapshots(
            deduplicated,
            provider="random",
            origin=origin,
            query_embedding=None,
            used_ids=used_ids,
            limit=limit,
        )

    def _score_snapshots(
        self,
        snapshots: Sequence[NodeSnapshot],
        *,
        provider: str,
        origin: NodeSnapshot | None,
        query_embedding: tuple[float, ...] | None,
        used_ids: set[int],
        limit: int,
    ) -> list[_CandidateEnvelope]:
        envelopes: list[_CandidateEnvelope] = []
        for snapshot in snapshots:
            if snapshot.id in used_ids:
                continue
            scored = self._score_snapshot(
                snapshot,
                provider=provider,
                origin=origin,
                query_embedding=query_embedding,
            )
            if scored is None:
                continue
            score, factors = scored
            envelopes.append(
                _CandidateEnvelope(
                    snapshot=snapshot,
                    provider=provider,
                    score=score,
                    factors=factors,
                )
            )
            if len(envelopes) >= limit:
                break
        return envelopes

    def _score_snapshot(
        self,
        snapshot: NodeSnapshot,
        *,
        provider: str,
        origin: NodeSnapshot | None,
        query_embedding: tuple[float, ...] | None,
    ) -> tuple[float, dict[str, float]] | None:
        factors: dict[str, float] = {}
        score = 0.0
        overlap = self._tag_overlap(origin, snapshot)
        if provider == "compass":
            similarity = 0.0
            if query_embedding and snapshot.embedding:
                similarity = max(
                    0.0, self._embedding_similarity(query_embedding, snapshot.embedding)
                )
            elif origin and origin.embedding and snapshot.embedding:
                similarity = max(
                    0.0,
                    self._embedding_similarity(origin.embedding, snapshot.embedding),
                )
            if similarity > 0:
                factors["similarity"] = similarity
            if overlap > 0:
                factors["tag_overlap"] = overlap
            score = similarity * self._base_weights.get(
                "tag_sim", 0.35
            ) + overlap * self._base_weights.get("diversity_bonus", 0.2)
        elif provider in {"echo", "curated"}:
            same_author = (
                1.0 if origin and origin.author_id == snapshot.author_id else 0.0
            )
            factors["author_match"] = same_author
            if overlap > 0:
                factors["tag_overlap"] = overlap
            score = (
                self._base_weights.get("echo", 0.25)
                + overlap * 0.1
                + same_author * 0.05
            )
        elif provider == "random":
            score = self._base_weights.get("fresh", 0.15)
            factors["baseline"] = score
        else:
            if overlap > 0:
                factors["tag_overlap"] = overlap
            score = max(0.05, overlap)
        score = float(score)
        if not math.isfinite(score) or score <= 0:
            score = 0.05
        normalized_factors = {
            key: float(value) for key, value in factors.items() if math.isfinite(value)
        }
        return score, normalized_factors

    def _tag_overlap(self, left: NodeSnapshot | None, right: NodeSnapshot) -> float:
        if left is None or not left.tags or not right.tags:
            return 0.0
        left_tags = {tag.lower() for tag in left.tags if tag}
        right_tags = {tag.lower() for tag in right.tags if tag}
        if not left_tags or not right_tags:
            return 0.0
        intersection = left_tags & right_tags
        if not intersection:
            return 0.0
        return len(intersection) / float(len(left_tags))

    def _finalize_candidates(
        self,
        envelopes: Sequence[_CandidateEnvelope],
        *,
        limit: int,
    ) -> list[TransitionCandidate]:
        if not envelopes:
            return []
        ordered = sorted(envelopes, key=lambda item: item.score, reverse=True)
        limited = ordered[:limit]
        total = sum(max(item.score, 0.0) for item in limited)
        if total <= 0:
            probability = 1.0 / len(limited)
            probabilities = [probability] * len(limited)
        else:
            probabilities = [max(item.score, 0.0) / total for item in limited]
        candidates: list[TransitionCandidate] = []
        for item, probability in zip(limited, probabilities, strict=False):
            factors = dict(item.factors)
            explain = self._format_explain(factors)
            badge = self._badges.get(item.provider, item.provider)
            candidates.append(
                TransitionCandidate(
                    node_id=item.snapshot.id,
                    provider=item.provider,
                    score=float(item.score),
                    probability=float(probability),
                    factors=factors,
                    badge=badge,
                    explain=explain,
                )
            )
        return candidates

    def _format_explain(self, factors: Mapping[str, float]) -> str:
        if not factors:
            return ""
        parts = []
        for key in sorted(factors):
            value = factors[key]
            parts.append(f"{key}={value:.2f}")
        return ", ".join(parts)

    def _build_telemetry(
        self,
        candidates: Sequence[TransitionCandidate],
        *,
        query_embedding: tuple[float, ...] | None,
    ) -> dict[str, float]:
        telemetry: dict[str, float] = {
            "candidates_total": float(len(candidates)),
            "query_embedding": 1.0 if query_embedding is not None else 0.0,
        }
        provider_counts: dict[str, int] = {}
        for candidate in candidates:
            provider_counts[candidate.provider] = (
                provider_counts.get(candidate.provider, 0) + 1
            )
        for provider, count in provider_counts.items():
            telemetry[f"provider_{provider}_count"] = float(count)
        return telemetry


__all__ = ["NavigationService", "NodeSnapshot"]
