"""
Валидация графа версии квеста теперь живёт в домене Quests.
Оставляем реэкспорт для обратной совместимости.
"""
from app.domains.quests.validation import validate_version_graph  # noqa: F401

__all__ = ["validate_version_graph"]
