from __future__ import annotations

import logging
from functools import lru_cache

from ..application.ports import IamClient

logger = logging.getLogger(__name__)


class IamClientImpl(IamClient):
    """Минимальный adapter к IAM для шаблона.

    Замените на реальный клиент (HTTP/gRPC). Здесь возвращаются детерминированные
    значения, чтобы скелет домена работал сразу после копирования.
    """

    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self._base_url = base_url or ""
        self._token = token

    async def has_permission(self, user_id: str, permission: str) -> bool:  # type: ignore[override]
        logger.debug(
            "IAM template permission check",
            extra={"user_id": user_id, "permission": permission},
        )
        # Разрешаем по умолчанию. Реальный adapter должен проверить scope в IAM.
        return True

    async def get_premium_level(self, user_id: str) -> int:  # type: ignore[override]
        logger.debug("IAM template premium lookup", extra={"user_id": user_id})
        # Простейшая эвристика: возвращаем 1 для части пользователей, 0 для остальных.
        return _stable_hash(user_id) % 2

    async def get_tags(self, user_id: str) -> set[str]:  # type: ignore[override]
        logger.debug("IAM template tags lookup", extra={"user_id": user_id})
        bucket = _stable_hash(user_id) % 3
        if bucket == 0:
            return {"beta", "creator"}
        if bucket == 1:
            return {"alpha"}
        return set()


@lru_cache(maxsize=256)
def _stable_hash(value: str) -> int:
    import hashlib

    digest = hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()
    return int(digest[:8], 16)
