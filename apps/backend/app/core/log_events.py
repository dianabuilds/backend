import logging
from collections import Counter, defaultdict
from typing import Dict

logger = logging.getLogger("app")

AUTH_SUCCESS = "AUTH_SUCCESS"
AUTH_FAILURE = "AUTH_FAILURE"
CACHE_HIT = "CACHE_HIT"
CACHE_MISS = "CACHE_MISS"
CACHE_INVALIDATE = "CACHE_INVALIDATE"
DB_SLOW = "DB_SLOW"
TRANSITION_START = "transition.start"
TRANSITION_FINISH = "transition.finish"
NO_ROUTE = "no_route"
FALLBACK_HIT = "fallback.hit"

# in-memory metrics for admin cache stats
cache_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: {"hit": 0, "miss": 0})
cache_key_hits: Counter[str] = Counter()


def cache_hit(component: str, key: str, user: str | None = None) -> None:
    logger.info(f"{CACHE_HIT} {component} key={key} user={user or '-'}")
    cache_counters[component]["hit"] += 1
    cache_key_hits[key] += 1


def cache_miss(component: str, key: str, user: str | None = None) -> None:
    logger.info(f"{CACHE_MISS} {component} key={key} user={user or '-'}")
    cache_counters[component]["miss"] += 1


def cache_invalidate(component: str, reason: str, key: str | None = None) -> None:
    logger.info(f"{CACHE_INVALIDATE} {component} reason={reason} key={key or '-'}")


def auth_success(user_id: str | None) -> None:
    logger.info(f"{AUTH_SUCCESS} user={user_id or '-'}")


def auth_failure(reason: str, user: str | None = None) -> None:
    logger.warning(f"{AUTH_FAILURE} reason={reason} user={user or '-'}")


def transition_start(node: str) -> None:
    logger.info(f"{TRANSITION_START} node={node}")


def transition_finish(node: str | None) -> None:
    logger.info(f"{TRANSITION_FINISH} node={node or '-'}")


def no_route(node: str) -> None:
    logger.warning(f"{NO_ROUTE} node={node}")


def fallback_hit(component: str) -> None:
    logger.warning(f"{FALLBACK_HIT} component={component}")
