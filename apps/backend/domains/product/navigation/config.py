from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModeConfig:
    name: str
    providers: tuple[str, ...]
    k_base: int
    temperature: float
    epsilon: float
    author_threshold: int
    tag_threshold: int
    allow_random: bool
    curated_boost: float = 0.6


DEFAULT_BASE_WEIGHTS: dict[str, float] = {
    "curated": 1.2,
    "tag_sim": 0.35,
    "echo": 0.25,
    "fresh": 0.15,
    "diversity_bonus": 0.2,
}

DEFAULT_BADGES_BY_PROVIDER: dict[str, str] = {
    "curated": "trail",
    "compass": "similar",
    "echo": "similar",
    "random": "explore",
}

DEFAULT_MODE_CONFIGS: dict[str, ModeConfig] = {
    "normal": ModeConfig(
        name="normal",
        providers=("curated", "compass", "echo", "random"),
        k_base=48,
        temperature=0.30,
        epsilon=0.05,
        author_threshold=3,
        tag_threshold=3,
        allow_random=True,
    ),
    "echo_boost": ModeConfig(
        name="echo_boost",
        providers=("curated", "compass", "echo"),
        k_base=48,
        temperature=0.25,
        epsilon=0.0,
        author_threshold=3,
        tag_threshold=3,
        allow_random=False,
    ),
    "discover": ModeConfig(
        name="discover",
        providers=("curated", "compass", "random"),
        k_base=64,
        temperature=0.50,
        epsilon=0.15,
        author_threshold=2,
        tag_threshold=2,
        allow_random=True,
    ),
    "editorial": ModeConfig(
        name="editorial",
        providers=("curated", "compass"),
        k_base=32,
        temperature=0.10,
        epsilon=0.0,
        author_threshold=4,
        tag_threshold=4,
        allow_random=False,
    ),
    "near_limit": ModeConfig(
        name="near_limit",
        providers=("curated", "compass", "echo"),
        k_base=36,
        temperature=0.20,
        epsilon=0.0,
        author_threshold=3,
        tag_threshold=3,
        allow_random=False,
    ),
    "lite": ModeConfig(
        name="lite",
        providers=("curated", "compass"),
        k_base=16,
        temperature=0.15,
        epsilon=0.0,
        author_threshold=4,
        tag_threshold=4,
        allow_random=False,
    ),
}


__all__ = [
    "ModeConfig",
    "DEFAULT_BASE_WEIGHTS",
    "DEFAULT_BADGES_BY_PROVIDER",
    "DEFAULT_MODE_CONFIGS",
]
