from __future__ import annotations

# Временный реэкспорт схем домена AI Quests для поэтапной локализации
from app.schemas.ai_quests import (  # noqa: F401
    GenerateQuestIn,
    GenerationEnqueued,
    GenerationJobOut,
    TickIn,
)

__all__ = ["GenerateQuestIn", "GenerationEnqueued", "GenerationJobOut", "TickIn"]
