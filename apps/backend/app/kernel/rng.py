from __future__ import annotations

import os
import random
import secrets

_CURRENT_SEED: int | None = None
_rng = random.Random()


def init_rng(strategy: str) -> int:
    """Initialise global RNG according to strategy."""
    global _CURRENT_SEED, _rng
    if strategy == "fixed":
        seed = int(os.getenv("RNG_SEED", "1"))
    else:
        env_seed = os.getenv("RNG_SEED")
        seed = int(env_seed) if env_seed is not None else secrets.randbits(32)
    random.seed(seed)
    _rng.seed(seed)
    _CURRENT_SEED = seed
    os.environ["RNG_SEED"] = str(seed)
    return seed


def next_seed() -> int:
    return _rng.randrange(1, 2**32)


def get_seed() -> int | None:
    return _CURRENT_SEED


__all__ = ["init_rng", "next_seed", "get_seed"]

