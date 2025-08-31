import os
import random
import secrets

_CURRENT_SEED: int | None = None
_rng = random.Random()


def init_rng(strategy: str) -> int:
    """Initialise global RNG according to strategy.

    When ``strategy`` is ``"fixed"`` the seed is taken from the ``RNG_SEED``
    environment variable or defaults to ``1``.  For any other strategy a seed is
    taken from ``RNG_SEED`` or generated randomly.  The chosen seed is applied to
    both Python's global ``random`` module and the internal RNG used by
    :func:`next_seed` so that reproducible seeds can be produced for previews and
    simulations.
    """
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
    """Return a new deterministic seed from the global RNG."""
    return _rng.randrange(1, 2**32)


def get_seed() -> int | None:
    """Return the seed used to initialise the RNG."""
    return _CURRENT_SEED


__all__ = ["init_rng", "next_seed", "get_seed"]
