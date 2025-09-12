from __future__ import annotations

# Aggregate DB infrastructure into kernel during migration.
# Re-export from providers to keep API intact.

from app.providers.db.session import (
    get_db,
    db_session,
    get_engine,
    get_session_factory,
    get_current_session,
    init_db,
    check_database_connection,
    close_db_connection,
)
from app.providers.db.base import Base
from app.providers.db.adapters import UUID, JSONB, ARRAY, VECTOR, STR_ID
from app.providers.db.pagination import (
    PageQuery,
    CursorPayload,
    parse_page_query,
    encode_cursor,
    decode_cursor,
    build_cursor_for_last_item,
    apply_sorting,
    apply_pagination,
    fetch_page,
    extract_filters,
    apply_filters,
    scope_by_profile,
)

__all__ = [
    # sessions/engine
    "get_db",
    "db_session",
    "get_engine",
    "get_session_factory",
    "get_current_session",
    "init_db",
    "check_database_connection",
    "close_db_connection",
    # base/adapters
    "Base",
    "UUID",
    "JSONB",
    "ARRAY",
    "VECTOR",
    "STR_ID",
    # pagination helpers
    "PageQuery",
    "CursorPayload",
    "parse_page_query",
    "encode_cursor",
    "decode_cursor",
    "build_cursor_for_last_item",
    "apply_sorting",
    "apply_pagination",
    "fetch_page",
    "extract_filters",
    "apply_filters",
    "scope_by_profile",
]

