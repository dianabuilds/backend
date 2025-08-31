"""
Domains.AI: Pipeline re-export.

Позволяет импортировать пайплайн как:
from app.domains.ai.pipeline import run_full_generation
"""

from .pipeline_impl import run_full_generation  # noqa: F401

__all__ = ["run_full_generation"]
