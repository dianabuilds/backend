from __future__ import annotations

# Временный адаптер: реэкспортируем существующий роутер из app/api
from app.api.admin_moderation_cases import router  # type: ignore  # thin domain adapter

__all__ = ["router"]
