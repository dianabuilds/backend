from __future__ import annotations

# Доменная обёртка: реэкспортируем валидатор из домена Quests
from app.domains.quests.api.admin_validation_router import router  # re-export
