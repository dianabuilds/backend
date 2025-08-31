from __future__ import annotations

from app.domains.quests.api.admin_validation_router import (
    router as quests_admin_validation_router,
)

router = quests_admin_validation_router

# Доменная обёртка: реэкспортируем валидатор из домена Quests
