from __future__ import annotations

# Standalone SQLAlchemy type adapters to avoid importing app.models package (prevents circular imports)
import os
import uuid
from typing import Any, Dict, Optional, Union

from sqlalchemy.dialects.postgresql import JSONB as pg_JSONB, UUID as pg_UUID, TSVECTOR as pg_TSVECTOR
from sqlalchemy.types import JSON, TypeDecorator, CHAR
import sqlalchemy.types as types


class UUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified UUID.
    """

    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(pg_UUID())
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(str(value))


class JSONB(TypeDecorator):
    """JSON/JSONB compatibility type.

    Uses PostgreSQL JSONB if available, otherwise falls back to generic JSON.
    """

    impl = JSON

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(pg_JSONB())
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return value


class ARRAY(TypeDecorator):
    """Simple ARRAY emulation for SQLite compatibility.

    Stores lists as JSON on non-PostgreSQL backends.
    """

    impl = JSON

    def __init__(self, item_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return types.ARRAY(self.item_type)
        return JSON()

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        # For SQLite/others store as JSON-compatible list
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        # Already a list from JSON
        return value


class VECTOR(TypeDecorator):
    """Vector type adapter. For PostgreSQL uses TSVECTOR or vector extension; otherwise stores as JSON."""

    impl = JSON

    def __init__(self, dim: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        # If pgvector extension installed you could return that type here.
        if dialect.name == "postgresql":
            # Fallback to TSVECTOR to avoid hard dependency on pgvector in tests
            return dialect.type_descriptor(pg_TSVECTOR())
        return JSON()

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            # For real implementation, convert to tsvector/pgvector input format
            if isinstance(value, (list, tuple)):
                return " ".join(map(str, value))
            return str(value)
        # For non-PG store as JSON list
        if isinstance(value, (list, tuple)):
            return list(value)
        return [value]

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            # Return raw string; parsing left to application
            if isinstance(value, bytes):
                return value.decode("utf-8")
            return value
        return value


class TSVector(TypeDecorator):
    """Text search vector stub for compatibility in tests."""

    impl = JSON

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(pg_TSVECTOR())
        return JSON()


__all__ = [
    "UUID",
    "JSONB",
    "ARRAY",
    "VECTOR",
    "TSVector",
]
