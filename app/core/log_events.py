import logging

logger = logging.getLogger("app")


AUTH_SUCCESS = "AUTH_SUCCESS"
AUTH_FAILURE = "AUTH_FAILURE"
CACHE_HIT = "CACHE_HIT"
CACHE_MISS = "CACHE_MISS"
CACHE_INVALIDATE = "CACHE_INVALIDATE"
DB_SLOW = "DB_SLOW"


def cache_hit(component: str, key: str, user: str | None = None) -> None:
    logger.info(f"{CACHE_HIT} {component} key={key} user={user or '-'}")


def cache_miss(component: str, key: str, user: str | None = None) -> None:
    logger.info(f"{CACHE_MISS} {component} key={key} user={user or '-'}")


def cache_invalidate(component: str, reason: str, key: str | None = None) -> None:
    logger.info(f"{CACHE_INVALIDATE} {component} reason={reason} key={key or '-'}")


def auth_success(user_id: str | None) -> None:
    logger.info(f"{AUTH_SUCCESS} user={user_id or '-'}")


def auth_failure(reason: str, user: str | None = None) -> None:
    logger.warning(f"{AUTH_FAILURE} reason={reason} user={user or '-'}")

