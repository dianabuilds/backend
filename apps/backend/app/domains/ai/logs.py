"""
Domains.AI: Logs re-export.

from app.domains.ai.logs import save_stage_log
"""
from .logs_impl import save_stage_log  # noqa: F401
from app.domains.ai.infrastructure.models.generation_models import GenerationJobLog  # noqa: F401

__all__ = ["save_stage_log", "GenerationJobLog"]
