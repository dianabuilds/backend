"""
РђРґР°РїС‚РµСЂС‹ С‚РёРїРѕРІ РґР°РЅРЅС‹С… SQLAlchemy РґР»СЏ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё РјРµР¶РґСѓ PostgreSQL Рё SQLite.
"""

from __future__ import annotations

import uuid

import sqlalchemy.types as types
from sqlalchemy.dialects.postgresql import JSONB as pg_JSONB
from sqlalchemy.dialects.postgresql import TSVECTOR as pg_TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as pg_UUID
from sqlalchemy.types import CHAR, TypeDecorator




class UUID(TypeDecorator):
    """РЈРЅРёРІРµСЂСЃР°Р»СЊРЅС‹Р№ С‚РёРї UUID РґР»СЏ СЂР°Р·РЅС‹С… Р±Р°Р· РґР°РЅРЅС‹С…."""

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
    РЈРЅРёРІРµСЂСЃР°Р»СЊРЅС‹Р№ С‚РёРї JSONB РґР»СЏ СЂР°Р·РЅС‹С… Р±Р°Р· РґР°РЅРЅС‹С….
    РСЃРїРѕР»СЊР·СѓРµС‚ JSONB РІ PostgreSQL Рё Text РІ SQLite Рё С‚РµСЃС‚Р°С….
    """

    impl = types.Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(pg_JSONB())
        else:
            return dialect.type_descriptor(types.Text())

    def process_bind_param(self, value, dialect):
        import json

        if value is not None:
            # РџСЂРµРѕР±СЂР°Р·СѓРµРј РІ JSON СЃС‚СЂРѕРєСѓ, РµСЃР»Рё СЌС‚Рѕ РЅРµ СЃС‚СЂРѕРєР°
            if not isinstance(value, str):
                return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        import json

        if value is not None:
            # РџС‹С‚Р°РµРјСЃСЏ РїСЂРµРѕР±СЂР°Р·РѕРІР°С‚СЊ СЃС‚СЂРѕРєСѓ РІ РѕР±СЉРµРєС‚ JSON
            try:
                return json.loads(value)
            except (TypeError, json.JSONDecodeError):
                return value
        return value


class ARRAY(TypeDecorator):
    """РЈРЅРёРІРµСЂСЃР°Р»СЊРЅС‹Р№ С‚РёРї ARRAY РґР»СЏ СЂР°Р·РЅС‹С… Р±Р°Р· РґР°РЅРЅС‹С….

    РСЃРїРѕР»СЊР·СѓРµС‚ PostgreSQL ARRAY, Р° РІ SQLite С…СЂР°РЅРёС‚ РґР°РЅРЅС‹Рµ РєР°Рє JSON-СЃС‚СЂРѕРєСѓ.
    """

    impl = types.Text
    cache_ok = True

    def __init__(self, item_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import ARRAY as pg_ARRAY

            return dialect.type_descriptor(pg_ARRAY(self.item_type))
        else:
            return dialect.type_descriptor(types.Text())

    def process_bind_param(self, value, dialect):
        import json

        # Р”Р»СЏ SQLite/С‚РµСЃС‚РѕРІ С…СЂР°РЅРёРј РєР°Рє JSON-СЃС‚СЂРѕРєСѓ, РґР»СЏ PostgreSQL вЂ” РѕС‚РґР°С‘Рј РєР°Рє РµСЃС‚СЊ
        if dialect.name != "postgresql" :
            if value is not None and not isinstance(value, str):
                return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        import json

        if value is None:
            return None

        # РћРїСЂРµРґРµР»СЏРµРј, РЅСѓР¶РЅРѕ Р»Рё РїСЂРёРІРѕРґРёС‚СЊ СЌР»РµРјРµРЅС‚С‹ Рє С‡РёСЃР»Сѓ
        is_numeric = False
        try:
            is_numeric = issubclass(self.item_type, types.Integer | types.Float | types.Numeric)
        except Exception:
            is_numeric = False

        if dialect.name == "postgresql":
            # Р’ PostgreSQL РґСЂР°Р№РІРµСЂ РѕР±С‹С‡РЅРѕ РІРѕР·РІСЂР°С‰Р°РµС‚ СѓР¶Рµ Python-СЃРїРёСЃРѕРє
            if isinstance(value, list | tuple):
                if is_numeric:
                    try:
                        return [float(x) for x in value]
                    except Exception:
                        return list(value)
                # СЃС‚СЂРѕРєРѕРІС‹Рµ Рё РїСЂРѕС‡РёРµ С‚РёРїС‹ РІРѕР·РІСЂР°С‰Р°РµРј РєР°Рє РµСЃС‚СЊ
                return list(value)
            # РќР° РІСЃСЏРєРёР№ СЃР»СѓС‡Р°Р№: РµСЃР»Рё РїСЂРёС€Р»Р° СЃС‚СЂРѕРєР° вЂ” РїС‹С‚Р°РµРјСЃСЏ СЂР°СЃРїР°СЂСЃРёС‚СЊ JSON
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

        # Р’ SQLite/С‚РµСЃС‚Р°С… С‡РёС‚Р°РµРј JSON-С‚РµРєСЃС‚
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
        if dialect.name == "postgresql":
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

        # РќРѕСЂРјР°Р»РёР·СѓРµРј numpy.ndarray -> list
        try:
            if hasattr(value, "tolist"):
                value = value.tolist()  # type: ignore[assignment]
        except Exception:
            pass

        # Р’ PostgreSQL pgvector РѕР¶РёРґР°РµС‚ СЃРїРёСЃРѕРє С‡РёСЃРµР», Р° РЅРµ JSON-СЃС‚СЂРѕРєСѓ
        if dialect.name == "postgresql":
            try:
                return [float(x) for x in value]  # type: ignore[iterable]
            except Exception:
                # РµСЃР»Рё РїСЂРёС€Р»Р° СЃС‚СЂРѕРєР° СЃ JSON, РїРѕРїСЂРѕР±СѓРµРј СЂР°СЃРїР°СЂСЃРёС‚СЊ
                if isinstance(value, str):
                    try:
                        arr = json.loads(value)
                        return [float(x) for x in arr]
                    except Exception:
                        pass
                return value
        # Р’ SQLite/С‚РµСЃС‚Р°С… С…СЂР°РЅРёРј РєР°Рє JSON-С‚РµРєСЃС‚
        if not isinstance(value, str):
            try:
                return json.dumps(value)
            except Exception:
                # РЅР° РєСЂР°Р№РЅРёР№ СЃР»СѓС‡Р°Р№ вЂ” РєРѕРЅРІРµСЂС‚РёСЂСѓРµРј Рє СЃРїРёСЃРєСѓ СЃС‚СЂРѕРє
                try:
                    return json.dumps(list(value))  # type: ignore[arg-type]
                except Exception:
                    return json.dumps([])
        return value

    def process_result_value(self, value, dialect):
        import json

        if value is None:
            return None

        # РќРѕСЂРјР°Р»РёР·СѓРµРј РІРѕР·РјРѕР¶РЅС‹Р№ numpy.ndarray РІ СЃРїРёСЃРѕРє
        try:
            if hasattr(value, "tolist"):
                value = value.tolist()  # type: ignore[assignment]
        except Exception:
            pass

        if dialect.name == "postgresql":
            # Р”СЂР°Р№РІРµСЂ РјРѕР¶РµС‚ РІРµСЂРЅСѓС‚СЊ list/tuple (РёР»Рё np.ndarray, РѕР±СЂР°Р±РѕС‚Р°РЅ РІС‹С€Рµ)
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

        # SQLite/С‚РµСЃС‚С‹: С‡РёС‚Р°РµРј JSONвЂ‘СЃС‚СЂРѕРєСѓ, РїСЂРёРІРѕРґРёРј Рє СЃРїРёСЃРєСѓ
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

        # РќР° РІСЃСЏРєРёР№ СЃР»СѓС‡Р°Р№ вЂ” РµСЃР»Рё РїСЂРёС€С‘Р» СѓР¶Рµ СЃРїРёСЃРѕРє/РєРѕСЂС‚РµР¶
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
        if dialect.name == "postgresql":
            return dialect.type_descriptor(pg_TSVECTOR())
        return dialect.type_descriptor(types.Text())
