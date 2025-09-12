from __future__ import annotations

import logging
from collections import Counter, defaultdict

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
FALLBACK_USED = "fallback.used"

# Node lifecycle events
NODE_CREATE_START = "node.create.start"
NODE_CREATE_SUCCESS = "node.create.success"
NODE_CREATE_FAIL = "node.create.fail"
NODE_AUTOSAVE_OK = "node.autosave.ok"
NODE_AUTOSAVE_FAIL = "node.autosave.fail"
NODE_COVER_UPLOAD_START = "node.cover_upload.start"
NODE_COVER_UPLOAD_SUCCESS = "node.cover_upload.success"
NODE_COVER_UPLOAD_FAIL = "node.cover_upload.fail"
NODE_PUBLISH_START = "node.publish.start"
NODE_PUBLISH_SUCCESS = "node.publish.success"
NODE_PUBLISH_FAIL = "node.publish.fail"

# in-memory metrics for admin cache stats
cache_counters: dict[str, dict[str, int]] = defaultdict(lambda: {"hit": 0, "miss": 0})
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


def fallback_used(component: str) -> None:
    logger.info(f"{FALLBACK_USED} component={component}")


# Node lifecycle logging helpers -------------------------------------------
def node_create_start(user: str | None, node_type: str | None) -> None:
    logger.info(f"{NODE_CREATE_START} user={user or '-'} type={node_type or '-'}")


def node_create_success(node_id: str, user: str | None) -> None:
    logger.info(f"{NODE_CREATE_SUCCESS} node={node_id} user={user or '-'}")


def node_create_fail(user: str | None, reason: str) -> None:
    logger.warning(f"{NODE_CREATE_FAIL} user={user or '-'} reason={reason}")


def node_autosave_ok(node_id: str, user: str | None) -> None:
    logger.info(f"{NODE_AUTOSAVE_OK} node={node_id} user={user or '-'}")


def node_autosave_fail(node_id: str | None, user: str | None, reason: str) -> None:
    logger.warning(f"{NODE_AUTOSAVE_FAIL} node={node_id or '-'} user={user or '-'} reason={reason}")


def node_cover_upload_start(user: str | None) -> None:
    logger.info(f"{NODE_COVER_UPLOAD_START} user={user or '-'}")


def node_cover_upload_success(user: str | None) -> None:
    logger.info(f"{NODE_COVER_UPLOAD_SUCCESS} user={user or '-'}")


def node_cover_upload_fail(user: str | None, reason: str) -> None:
    logger.warning(f"{NODE_COVER_UPLOAD_FAIL} user={user or '-'} reason={reason}")


def node_publish_start(node_id: str, user: str | None) -> None:
    logger.info(f"{NODE_PUBLISH_START} node={node_id} user={user or '-'}")


def node_publish_success(node_id: str, user: str | None) -> None:
    logger.info(f"{NODE_PUBLISH_SUCCESS} node={node_id} user={user or '-'}")


def node_publish_fail(node_id: str | None, user: str | None, reason: str) -> None:
    logger.warning(f"{NODE_PUBLISH_FAIL} node={node_id or '-'} user={user or '-'} reason={reason}")

