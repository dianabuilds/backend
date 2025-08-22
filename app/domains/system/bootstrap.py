from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Временная прокладка: не теряем поведение, переводим точку импорта на домен.
# После подтверждения поведения можно перенести реализацию сюда и удалить legacy.
async def ensure_default_admin() -> None:
    try:
        from app.services.bootstrap import ensure_default_admin as _legacy_ensure_default_admin
        await _legacy_ensure_default_admin()
    except Exception as e:
        logger.warning("ensure_default_admin legacy call failed: %s", e)
