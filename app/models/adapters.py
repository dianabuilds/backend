"""
Адаптеры типов данных SQLAlchemy для совместимости между PostgreSQL и SQLite.
"""
import os
import uuid
from typing import Any, Dict, Optional, Union

from sqlalchemy.dialects.postgresql import JSONB as pg_JSONB, UUID as pg_UUID, TSVECTOR as pg_TSVECTOR
from sqlalchemy.types import JSON, TypeDecorator, CHAR
import sqlalchemy.types as types

# Определяем, находимся ли мы в тестовой среде
IS_TESTING = os.environ.get("TESTING", "").lower() in ("true", "1", "t")


class UUID(TypeDecorator):
    """Универсальный тип UUID для разных баз данных."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(pg_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


class JSONB(TypeDecorator):
    """
    Универсальный тип JSONB для разных баз данных.
    Использует JSONB в PostgreSQL и Text в SQLite и тестах.
    """

    impl = types.Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql' and not IS_TESTING:
            return dialect.type_descriptor(pg_JSONB())
        else:
            return dialect.type_descriptor(types.Text())

    def process_bind_param(self, value, dialect):
        import json
        if value is not None:
            # Преобразуем в JSON строку, если это не строка
            if not isinstance(value, str):
                return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        import json
        if value is not None:
            # Пытаемся преобразовать строку в объект JSON
            try:
                return json.loads(value)
            except (TypeError, json.JSONDecodeError):
                return value
        return value


class ARRAY(TypeDecorator):
    """Универсальный тип ARRAY для разных баз данных.

    Использует PostgreSQL ARRAY, а в SQLite хранит данные как JSON-строку.
    """

    impl = types.Text
    cache_ok = True

    def __init__(self, item_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and not IS_TESTING:
            from sqlalchemy.dialects.postgresql import ARRAY as pg_ARRAY

            return dialect.type_descriptor(pg_ARRAY(self.item_type))
        else:
            return dialect.type_descriptor(types.Text())

    def process_bind_param(self, value, dialect):
        import json

        if value is not None and not isinstance(value, str):
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        import json

        if value is None:
            return None

        # В PostgreSQL pgvector уже возвращает массив чисел
        if dialect.name == "postgresql" and not IS_TESTING:
            if isinstance(value, (list, tuple)):
                return [float(x) for x in value]
            # если по какой-то причине вернулась строка — пробуем распарсить
            if isinstance(value, str):
                try:
                    arr = json.loads(value)
                    return [float(x) for x in arr] if isinstance(arr, (list, tuple)) else arr
                except Exception:
                    return value
            return value

        # В SQLite/тестах читаем JSON-текст
        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return value


class VECTOR(TypeDecorator):
    """Simple vector type compatible with PostgreSQL pgvector and SQLite.

    In PostgreSQL environments (outside of tests) it uses the native pgvector
    type. For SQLite and tests it falls back to storing the vector as a JSON
    encoded string.
    """

    impl = types.Text
    cache_ok = True

    def __init__(self, dim: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and not IS_TESTING:
            try:  # pragma: no cover - pgvector may not be installed in tests
                from pgvector.sqlalchemy import Vector

                return dialect.type_descriptor(Vector(self.dim))
            except Exception:  # pragma: no cover
                pass
        return dialect.type_descriptor(types.Text())

    def process_bind_param(self, value, dialect):
        import json

        if value is None:
            return None

        # В PostgreSQL pgvector ожидает список чисел, а не JSON-строку
        if dialect.name == "postgresql" and not IS_TESTING:
            try:
                return [float(x) for x in value]  # type: ignore[iterable]
            except Exception:
                # если пришла строка с JSON, попробуем распарсить
                if isinstance(value, str):
                    try:
                        arr = json.loads(value)
                        return [float(x) for x in arr]
                    except Exception:
                        pass
                return value
        # В SQLite/тестах храним как JSON-текст
        if not isinstance(value, str):
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        import json

        if value is not None:
            try:
                return json.loads(value)
            except (TypeError, json.JSONDecodeError):
                return value
        return value


class TSVector(TypeDecorator):
    """Universal tsvector type compatible with PostgreSQL and SQLite.

    In PostgreSQL it uses the native TSVECTOR type while in SQLite (used in
    tests) it falls back to plain text. This allows defining tsvector columns
    without breaking schema creation in tests.
    """

    impl = types.Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and not IS_TESTING:
            return dialect.type_descriptor(pg_TSVECTOR())
        return dialect.type_descriptor(types.Text())
