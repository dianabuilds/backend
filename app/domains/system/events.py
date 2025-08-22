from __future__ import annotations

# Thin proxy: реэкспортируем события/шину и регистрацию обработчиков из services
from app.services.events import (  # noqa: F401
    register_handlers,
    get_event_bus,
    NodeCreated,
    NodeUpdated,
)

__all__ = ["register_handlers", "get_event_bus", "NodeCreated", "NodeUpdated"]
