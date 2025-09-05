from __future__ import annotations

# ruff: noqa: E402
from fastapi import APIRouter

# Агрегирующий роутер домена AI.
# Префикса не задаём, чтобы сохранить текущие URL (/admin/ai/...).
router = APIRouter()

# Подключаем доменные административные эндпоинты AI (где доступны)
from app.domains.ai.api.admin_quests_details_router import (
    router as admin_ai_quests_details_router,  # noqa: E402
)
from app.domains.ai.api.admin_quests_jobs_cursor_router import (
    router as admin_ai_quests_jobs_cursor_router,  # noqa: E402
)
from app.domains.ai.api.admin_quests_jobs_paged_router import (
    router as admin_ai_quests_jobs_paged_router,  # noqa: E402
)
from app.domains.ai.api.admin_quests_logs_router import (
    router as admin_ai_quests_logs_router,  # noqa: E402
)

# Временные доменные обёртки над legacy-ручками до полного переноса реализации
# Основной роутер AI-квестов
from app.domains.ai.api.admin_quests_router import (
    router as admin_ai_quests_router,  # noqa: E402
)
from app.domains.ai.api.admin_rate_limits_router import (
    router as admin_ai_rate_limits_router,  # noqa: E402
)
from app.domains.ai.api.settings_router import (  # noqa: E402
    router as admin_ai_settings_router,
)
from app.domains.ai.api.stats_router import (
    router as admin_ai_stats_router,  # noqa: E402
)
from app.domains.ai.api.system_defaults_router import (  # noqa: E402
    router as admin_ai_system_defaults_router,
)
from app.domains.ai.api.system_models_router import (  # noqa: E402
    router as admin_ai_system_models_router,
)
from app.domains.ai.api.system_prices_router import (  # noqa: E402
    router as admin_ai_system_prices_router,
)
from app.domains.ai.api.system_providers_router import (  # noqa: E402
    router as admin_ai_system_providers_router,
)
from app.domains.ai.api.usage_router import (
    router as admin_ai_usage_router,  # noqa: E402
)
from app.domains.ai.api.user_pref_router import (
    router as admin_ai_user_pref_router,  # noqa: E402
)

# Ручки валидации могут отсутствовать, поэтому импортируем их опционально
try:  # noqa: SIM105
    from app.domains.ai.api.admin_validation_router import (  # noqa: E402
        router as admin_ai_validation_router,
    )
except ModuleNotFoundError:  # pragma: no cover - отсутствует в тестовой среде
    admin_ai_validation_router = None

from app.domains.ai.api.embedding_router import (
    router as admin_embedding_router,  # noqa: E402
)

router.include_router(admin_ai_quests_router)
router.include_router(admin_ai_quests_logs_router)
router.include_router(admin_ai_quests_details_router)
router.include_router(admin_ai_quests_jobs_paged_router)
router.include_router(admin_ai_quests_jobs_cursor_router)
router.include_router(admin_ai_rate_limits_router)
router.include_router(admin_ai_stats_router)
if admin_ai_validation_router is not None:
    router.include_router(admin_ai_validation_router)
router.include_router(admin_embedding_router)
router.include_router(admin_ai_settings_router)
router.include_router(admin_ai_system_providers_router)
router.include_router(admin_ai_user_pref_router)
router.include_router(admin_ai_usage_router)
router.include_router(admin_ai_system_models_router)
router.include_router(admin_ai_system_prices_router)
router.include_router(admin_ai_system_defaults_router)
