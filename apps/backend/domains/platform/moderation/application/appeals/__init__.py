from __future__ import annotations

from . import commands as appeal_commands
from . import queries as appeal_queries
from .presenter import (
    build_appeals_list_response,
    build_decision_response,
    build_list_response,
    merge_appeal_with_db,
    record_to_dto,
)
from .repository import AppealsRepository, create_repository

list_appeals = appeal_queries.list_appeals
get_appeal = appeal_queries.get_appeal
decide_appeal = appeal_commands.decide_appeal

__all__ = [
    "AppealsRepository",
    "build_appeals_list_response",
    "build_decision_response",
    "build_list_response",
    "create_repository",
    "decide_appeal",
    "get_appeal",
    "list_appeals",
    "merge_appeal_with_db",
    "record_to_dto",
]
