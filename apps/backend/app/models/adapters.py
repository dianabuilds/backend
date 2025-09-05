"""
Адаптеры типов данных SQLAlchemy для совместимости между PostgreSQL и SQLite.
"""

from __future__ import annotations

import uuid

import sqlalchemy.types as types
from sqlalchemy.dialects.postgresql import JSONB as pg_JSONB
from sqlalchemy.dialects.postgresql import TSVECTOR as pg_TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as pg_UUID
from sqlalchemy.types import CHAR, TypeDecorator

from app.core.policy import policy


class UUID(TypeDecorator):
    """Универсальный тип UUID для разных баз данных."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(pg_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
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
        if dialect.name == "postgresql" and policy.allow_write:
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
        if dialect.name == "postgresql" and policy.allow_write:
            from sqlalchemy.dialects.postgresql import ARRAY as pg_ARRAY

            return dialect.type_descriptor(pg_ARRAY(self.item_type))
        else:
            return dialect.type_descriptor(types.Text())

    def process_bind_param(self, value, dialect):
        import json

        # Для SQLite/тестов храним как JSON-строку, для PostgreSQL — отдаём как есть
        if dialect.name != "postgresql" or not policy.allow_write:
            if value is not None and not isinstance(value, str):
                return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        import json

        if value is None:
            return None

        # Определяем, нужно ли приводить элементы к числу
        is_numeric = False
        try:
            is_numeric = issubclass(
                self.item_type, types.Integer | types.Float | types.Numeric
            )
        except Exception:
            is_numeric = False

        if dialect.name == "postgresql" and policy.allow_write:
            # В PostgreSQL драйвер обычно возвращает уже Python-список
            if isinstance(value, list | tuple):
                if is_numeric:
                    try:
                        return [float(x) for x in value]
                    except Exception:
                        return list(value)
                # строковые и прочие типы возвращаем как есть
                return list(value)
            # На всякий случай: если пришла строка — пытаемся распарсить JSON
            if isinstance(value, str):
                try:
                    arr = json.loads(value)
                    if isinstance(arr, list | tuple):
                        if is_numeric:
                            try:
                                return [float(x) for x in arr]
                            except Exception:
                                return list(arr)
                        return [str(x) for x in arr]
                    return arr
                except Exception:
                    return value
            return value

        # В SQLite/тестах читаем JSON-текст
        try:
            arr = json.loads(value)
            if isinstance(arr, list | tuple):
                if is_numeric:
                    try:
                        return [float(x) for x in arr]
                    except Exception:
                        return list(arr)
                return [str(x) for x in arr]
            return arr
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
        if dialect.name == "postgresql" and policy.allow_write:
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

        # Нормализуем numpy.ndarray -> list
        try:
            if hasattr(value, "tolist"):
                value = value.tolist()  # type: ignore[assignment]
        except Exception:
            pass

        # В PostgreSQL pgvector ожидает список чисел, а не JSON-строку
        if dialect.name == "postgresql" and policy.allow_write:
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
            try:
                return json.dumps(value)
            except Exception:
                # на крайний случай — конвертируем к списку строк
                try:
                    return json.dumps(list(value))  # type: ignore[arg-type]
                except Exception:
                    return json.dumps([])
        return value

    def process_result_value(self, value, dialect):
        import json

        if value is None:
            return None

        # Нормализуем возможный numpy.ndarray в список
        try:
            if hasattr(value, "tolist"):
                value = value.tolist()  # type: ignore[assignment]
        except Exception:
            pass

        if dialect.name == "postgresql" and policy.allow_write:
            # Драйвер может вернуть list/tuple (или np.ndarray, обработан выше)
            if isinstance(value, list | tuple):
                try:
                    return [float(x) for x in value]
                except Exception:
                    return list(value)
            if isinstance(value, str):
                try:
                    arr = json.loads(value)
                    if isinstance(arr, list | tuple):
                        try:
                            return [float(x) for x in arr]
                        except Exception:
                            return list(arr)
                    return arr
                except Exception:
                    return value
            return value

        # SQLite/тесты: читаем JSON‑строку, приводим к списку
        if isinstance(value, str):
            try:
                arr = json.loads(value)
                if isinstance(arr, list | tuple):
                    try:
                        return [float(x) for x in arr]
                    except Exception:
                        return list(arr)
                return arr
            except (TypeError, json.JSONDecodeError):
                return value

        # На всякий случай — если пришёл уже список/кортеж
        if isinstance(value, list | tuple):
            return list(value)

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
        if dialect.name == "postgresql" and policy.allow_write:
            return dialect.type_descriptor(pg_TSVECTOR())
        return dialect.type_descriptor(types.Text())
