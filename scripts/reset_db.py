import asyncio
import importlib
import os
import pkgutil
import sys
from pathlib import Path
from typing import Iterable, Set

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# Добавляем корневую директорию проекта в PYTHONPATH
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))


def _log(msg: str) -> None:
    print(f"[reset-db] {msg}")


def _is_production() -> bool:
    # Пытаемся взять окружение из настроек, если есть; иначе используем переменные окружения
    try:
        from apps.backend.app.core.config import settings  # type: ignore
        env = getattr(settings, "environment", None) or os.getenv("APP_ENV") or os.getenv("ENV")
    except Exception:
        env = os.getenv("APP_ENV") or os.getenv("ENV")
    env = (env or "").lower()
    return env in {"prod", "production"}


def _ensure_not_production() -> None:
    if _is_production() and os.getenv("FORCE_RESET") != "1":
        raise RuntimeError(
            "Запуск в production запрещён. Установите FORCE_RESET=1, если вы действительно уверены."
        )


def _get_database_url() -> str:
    # Предпочитаем async URL; иначе пробуем обычную переменную
    url = (
        os.getenv("ASYNC_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or "sqlite+aiosqlite:///test.db"
    )
    return url


def _normalize_pg_url(url: str) -> str:
    # Если указан postgresql:// без драйвера — переключим на asyncpg
    if url.startswith("postgres://"):
        url = "postgresql" + url[len("postgres") :]
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _detect_is_postgres(engine: AsyncEngine) -> bool:
    try:
        name = engine.url.get_backend_name()
    except Exception:
        try:
            name = str(engine.url).split(":", 1)[0]
        except Exception:
            name = ""
    return name.startswith("postgresql")


def _import_all_models() -> None:
    """
    Импортирует все модули внутри apps.backend.app.models, чтобы зарегистрировать все ORM-классы в MetaData.
    """
    try:
        pkg = importlib.import_module("apps.backend.app.models")
    except Exception as e:
        _log(f"Не удалось импортировать пакет apps.backend.app.models: {e}")
        return

    if not hasattr(pkg, "__path__"):
        return

    for finder, name, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        try:
            importlib.import_module(name)
        except Exception as e:
            _log(f"Предупреждение: не удалось импортировать {name}: {e}")


def _collect_all_metadatas() -> Set[sa.MetaData]:
    """
    Ищет все метаданные у ORM-классов, загруженных в sys.modules.
    Собирает уникальные объекты MetaData, чтобы выполнить create_all по каждому.
    """
    metas: Set[sa.MetaData] = set()
    for module in list(sys.modules.values()):
        try:
            d = getattr(module, "__dict__", None)
            if not isinstance(d, dict):
                continue
            for val in d.values():
                table = getattr(val, "__table__", None)
                if table is not None and hasattr(table, "metadata"):
                    metas.add(table.metadata)
        except Exception:
            continue
    return metas


def _get_target_schema() -> str:
    # Имя целевой схемы: по умолчанию public
    sch = os.getenv("DB_SCHEMA") or "public"
    # лёгкая нормализация
    return sch.strip() or "public"


async def _drop_everything(conn, is_postgres: bool) -> None:
    if is_postgres:
        target_schema = _get_target_schema()
        if target_schema == "public":
            # Полный сброс схемы public
            await conn.execute(sa.text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(sa.text("CREATE SCHEMA public"))
            # Права на всякий случай
            await conn.execute(sa.text("GRANT ALL ON SCHEMA public TO CURRENT_USER"))
            await conn.execute(sa.text("GRANT ALL ON SCHEMA public TO public"))
            # Выставляем search_path
            await conn.execute(sa.text("SET search_path TO public"))
        else:
            # Работаем только в целевой схеме; public не трогаем
            # Можно управлять удалением схемы через DROP_TARGET_SCHEMA=0/1 (по умолчанию 1)
            if (os.getenv("DROP_TARGET_SCHEMA") or "1") == "1":
                await conn.execute(sa.text(f"DROP SCHEMA IF EXISTS {sa.sql.quoted_name(target_schema, quote=True)} CASCADE"))
            await conn.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {sa.sql.quoted_name(target_schema, quote=True)}"))
            await conn.execute(sa.text(f"GRANT ALL ON SCHEMA {sa.sql.quoted_name(target_schema, quote=True)} TO CURRENT_USER"))
            await conn.execute(sa.text(f"GRANT ALL ON SCHEMA {sa.sql.quoted_name(target_schema, quote=True)} TO public"))
            # Включаем целевую схему в search_path
            await conn.execute(sa.text(f"SET search_path TO {sa.sql.quoted_name(target_schema, quote=True)}, public"))
    else:
        # Универсальный способ: отрефлектить и дропнуть все объекты
        tmp_meta = sa.MetaData()
        await conn.run_sync(tmp_meta.reflect)
        await conn.run_sync(tmp_meta.drop_all)


# ======================
# Пост-инициализация схемы
# ======================

async def _pg_enum_create_if_not_exists(conn, name: str, values: list[str]) -> None:
    # Создаём enum-типы, если отсутствуют, и добавляем недостающие значения
    exists = await conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = :n"), {"n": name})
    if exists.scalar() is None:
        vals = ", ".join([f"'{v}'" for v in values])
        await conn.execute(sa.text(f"CREATE TYPE {name} AS ENUM ({vals})"))
        return
    # Добавляем недостающие значения
    cur_vals = await conn.execute(
        sa.text(
            "SELECT enumlabel FROM pg_enum e "
            "JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = :n"
        ),
        {"n": name},
    )
    have = {r[0] for r in cur_vals.fetchall()}
    for v in values:
        if v not in have:
            try:
                await conn.execute(sa.text(f"ALTER TYPE {name} ADD VALUE IF NOT EXISTS '{v}'"))
            except Exception:
                # Старые версии PG без IF NOT EXISTS — пытаемся обычный ADD VALUE
                try:
                    await conn.execute(sa.text(f"ALTER TYPE {name} ADD VALUE '{v}'"))
                except Exception:
                    pass


async def _pg_enable_extensions(conn) -> None:
    await conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))


async def _index_exists(conn, index_name: str) -> bool:
    schema = _get_target_schema()
    res = await conn.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :n AND schemaname = :s"),
        {"n": index_name, "s": schema},
    )
    return res.scalar() is not None


async def _table_exists(conn, table: str) -> bool:
    schema = _get_target_schema()
    res = await conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_schema=:s AND table_name=:t"
        ),
        {"t": table, "s": schema},
    )
    return res.scalar() is not None


async def _column_exists(conn, table: str, column: str) -> bool:
    schema = _get_target_schema()
    res = await conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns WHERE table_schema=:s AND table_name=:t AND column_name=:c"
        ),
        {"t": table, "c": column, "s": schema},
    )
    return res.scalar() is not None


async def _add_column_if_missing(conn, table: str, col: str, type_sql: str, default_sql: str | None = None, not_null: bool = False) -> None:
    if not await _column_exists(conn, table, col):
        sql = f"ALTER TABLE {table} ADD COLUMN {col} {type_sql}"
        if default_sql:
            sql += f" DEFAULT {default_sql}"
        if not_null:
            sql += " NOT NULL"
        await conn.execute(sa.text(sql))


async def _ensure_nodes_shape(conn) -> None:
    # Обязательные поля для nodes
    # Булевы/числовые/JSON дефолты выставляем сразу (PG)
    await _add_column_if_missing(conn, "nodes", "allow_feedback", "BOOLEAN", "true", True)
    await _add_column_if_missing(conn, "nodes", "is_recommendable", "BOOLEAN", "true", True)
    await _add_column_if_missing(conn, "nodes", "popularity_score", "DOUBLE PRECISION", "0.0", True)
    await _add_column_if_missing(conn, "nodes", "is_visible", "BOOLEAN", "true", True)
    await _add_column_if_missing(conn, "nodes", "views", "INTEGER", "0", True)
    # JSONB поля
    await _add_column_if_missing(conn, "nodes", "reactions", "JSONB", "'{}'::jsonb", True)
    await _add_column_if_missing(conn, "nodes", "meta", "JSONB", "'{}'::jsonb", True)
    await _add_column_if_missing(conn, "nodes", "premium_only", "BOOLEAN", "false", True)
    await _add_column_if_missing(conn, "nodes", "ai_generated", "BOOLEAN", "false", True)
    # Вектор эмбеддингов
    await _add_column_if_missing(conn, "nodes", "embedding_vector", "vector(384)", None, False)
    # Индекс на slug (уникальный)
    if not await _index_exists(conn, "ix_nodes_slug"):
        await conn.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS ix_nodes_slug ON nodes (slug)"))
    # Индекс для эмбеддингов
    if await _column_exists(conn, "nodes", "embedding_vector") and not await _index_exists(conn, "idx_node_embedding_vector"):
        await conn.execute(
            sa.text(
                "CREATE INDEX IF NOT EXISTS idx_node_embedding_vector "
                "ON nodes USING ivfflat (embedding_vector vector_cosine_ops)"
            )
        )


async def _ensure_feedback(conn) -> None:
    # Таблица feedback + индексы
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS feedback (
          id uuid PRIMARY KEY,
          node_id uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
          author_id uuid NOT NULL REFERENCES users(id),
          nodes text NOT NULL,
          created_at timestamp DEFAULT now(),
          is_hidden boolean NOT NULL DEFAULT false,
          is_anonymous boolean NOT NULL DEFAULT false
        )
    """))
    if not await _index_exists(conn, "idx_feedback_node"):
        await conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_feedback_node ON feedback (node_id)"))
    if not await _index_exists(conn, "idx_feedback_author"):
        await conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_feedback_author ON feedback (author_id)"))


async def _ensure_tags(conn) -> None:
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS tags (
          id uuid PRIMARY KEY,
          slug varchar NOT NULL,
          name varchar NOT NULL,
          created_at timestamp DEFAULT now(),
          is_hidden boolean NOT NULL DEFAULT false
        )
    """))
    # Уникальный индекс на slug
    if not await _index_exists(conn, "idx_tag_slug"):
        await conn.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS idx_tag_slug ON tags (slug)"))

    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS node_tags (
          node_id uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
          tag_id uuid NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
          created_at timestamp DEFAULT now(),
          PRIMARY KEY (node_id, tag_id)
        )
    """))


async def _ensure_echo_trace(conn) -> None:
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS echo_trace (
          id uuid PRIMARY KEY,
          from_node_id uuid REFERENCES nodes(id),
          to_node_id uuid REFERENCES nodes(id),
          user_id uuid REFERENCES users(id),
          source text NULL,
          channel text NULL,
          created_at timestamp DEFAULT now()
        )
    """))
    if not await _index_exists(conn, "idx_echo_from_node"):
        await conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_echo_from_node ON echo_trace (from_node_id)"))


async def _ensure_node_traces(conn) -> None:
    await _pg_enum_create_if_not_exists(conn, "nodetracekind", ["auto", "manual", "quest_hint"])
    await _pg_enum_create_if_not_exists(conn, "nodetracevisibility", ["public", "private", "system"])
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS node_traces (
          id uuid PRIMARY KEY,
          node_id uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
          user_id uuid REFERENCES users(id),
          created_at timestamp NOT NULL DEFAULT now(),
          kind nodetracekind NOT NULL,
          comment text NULL,
          tags text[] NOT NULL DEFAULT '{}',
          visibility nodetracevisibility NOT NULL DEFAULT 'public'
        )
    """))
    if not await _index_exists(conn, "idx_node_traces_node"):
        await conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_node_traces_node ON node_traces (node_id)"))


async def _ensure_achievements(conn) -> None:
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS achievements (
          id uuid PRIMARY KEY,
          code varchar NOT NULL UNIQUE,
          title varchar NOT NULL,
          description text NULL,
          icon varchar NULL,
          condition jsonb NOT NULL,
          visible boolean NOT NULL DEFAULT true
        )
    """))
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS user_achievements (
          user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          achievement_id uuid NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
          unlocked_at timestamp NOT NULL DEFAULT now(),
          PRIMARY KEY (user_id, achievement_id)
        )
    """))
    if not await _index_exists(conn, "idx_user_achievements_user"):
        await conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_user_achievements_user ON user_achievements (user_id)"))
    if not await _index_exists(conn, "idx_user_achievements_achievement"):
        await conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_user_achievements_achievement ON user_achievements (achievement_id)"))


async def _ensure_event_quests(conn) -> None:
    await _pg_enum_create_if_not_exists(conn, "eventquestrewardtype", ["achievement", "premium", "custom"])
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS event_quests (
          id uuid PRIMARY KEY,
          title varchar NOT NULL,
          target_node_id uuid NOT NULL REFERENCES nodes(id),
          hints_tags text[] NOT NULL DEFAULT '{}',
          hints_keywords text[] NOT NULL DEFAULT '{}',
          hints_trace uuid[] NOT NULL DEFAULT '{}',
          starts_at timestamp NOT NULL,
          expires_at timestamp NOT NULL,
          max_rewards integer NOT NULL DEFAULT 0,
          reward_type eventquestrewardtype NOT NULL,
          is_active boolean NOT NULL DEFAULT false
        )
    """))
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS event_quest_completions (
          id uuid PRIMARY KEY,
          quest_id uuid NOT NULL REFERENCES event_quests(id) ON DELETE CASCADE,
          user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          node_id uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
          completed_at timestamp NOT NULL DEFAULT now(),
          UNIQUE (quest_id, user_id)
        )
    """))
    if not await _index_exists(conn, "idx_event_quest_completions_quest"):
        await conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_event_quest_completions_quest ON event_quest_completions (quest_id)"))


async def _ensure_roles_and_moderation(conn) -> None:
    # Роли и ограничения пользователей
    await _pg_enum_create_if_not_exists(conn, "user_role", ["user", "moderator", "admin"])
    await _pg_enum_create_if_not_exists(conn, "restriction_type", ["ban", "post_restrict"])

    # users.role / премиум-поля
    await _add_column_if_missing(conn, "users", "role", "user_role", "'user'", True)
    await _add_column_if_missing(conn, "users", "is_premium", "BOOLEAN", "false", True)
    await _add_column_if_missing(conn, "users", "premium_until", "timestamp", None, False)

    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS user_restrictions (
          id uuid PRIMARY KEY,
          user_id uuid NOT NULL REFERENCES users(id),
          type restriction_type NOT NULL,
          reason text NULL,
          created_at timestamp NULL,
          expires_at timestamp NULL,
          issued_by uuid NULL REFERENCES users(id)
        )
    """))
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS node_moderation (
          id uuid PRIMARY KEY,
          node_id uuid NULL REFERENCES nodes(id),
          reason text NULL,
          hidden_by uuid NULL REFERENCES users(id),
          created_at timestamp NULL
        )
    """))


async def _ensure_audit_logs(conn) -> None:
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS audit_logs (
          id uuid PRIMARY KEY,
          actor_id uuid NULL,
          action varchar NOT NULL,
          resource_type varchar NULL,
          resource_id varchar NULL,
          before jsonb NULL,
          after jsonb NULL,
          ip varchar NULL,
          user_agent varchar NULL,
          created_at timestamp NOT NULL DEFAULT now(),
          extra jsonb NULL
        )
    """))
    if not await _index_exists(conn, "idx_audit_logs_actor"):
        await conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs (actor_id)"))
    if not await _index_exists(conn, "idx_audit_logs_action"):
        await conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs (action)"))
    if not await _index_exists(conn, "idx_audit_logs_created"):
        await conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs (created_at)"))


async def _ensure_quests_search_vector(conn) -> None:
    # Добавляем tsvector, функцию и триггер, если есть таблица quests
    if not await _table_exists(conn, "quests"):
        return
    if not await _column_exists(conn, "quests", "search_vector"):
        await conn.execute(sa.text("ALTER TABLE quests ADD COLUMN search_vector tsvector"))
    # Функция обновления
    await conn.execute(sa.text("""
        CREATE OR REPLACE FUNCTION quests_search_vector_update() RETURNS trigger AS $$
        BEGIN
          NEW.search_vector :=
            to_tsvector('simple', coalesce(NEW.title, '') || ' ' || coalesce(NEW.subtitle, '') || ' ' || coalesce(NEW.description, ''));
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))
    # Индекс
    if not await _index_exists(conn, "idx_quests_search_vector"):
        await conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_quests_search_vector
            ON quests USING GIN(search_vector)
        """))
    # Триггер
    await conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'trg_quests_search_vector'
            ) THEN
                CREATE TRIGGER trg_quests_search_vector
                BEFORE INSERT OR UPDATE ON quests
                FOR EACH ROW
                EXECUTE FUNCTION quests_search_vector_update();
            END IF;
        END$$;
    """))


async def _drop_legacy_columns(conn) -> None:
    # Удаляем устаревшие элементы схемы, которые больше не используются приложением
    # 1) Устаревшая колонка nodes.tags (если используете связь через node_tags)
    if await _column_exists(conn, "nodes", "tags"):
        try:
            await conn.execute(sa.text("ALTER TABLE nodes DROP COLUMN tags"))
        except Exception:
            pass


async def _post_create_schema_fixes(conn, is_postgres: bool) -> None:
    if not is_postgres:
        # Для не-PG минимальные гарантии (в основном dev на SQLite) — пропускаем сложные объекты
        return

    # 1) Расширения PG
    await _pg_enable_extensions(conn)

    # 2) Узлы (nodes) — ключевые поля и индексы
    await _ensure_nodes_shape(conn)

    # 3) Таблицы вокруг контента/навигации
    await _ensure_feedback(conn)
    await _ensure_tags(conn)
    await _ensure_echo_trace(conn)
    await _ensure_node_traces(conn)

    # 4) Достижения/эвент-квесты
    await _ensure_achievements(conn)
    await _ensure_event_quests(conn)

    # 5) Роли/модерация/премиум
    await _ensure_roles_and_moderation(conn)

    # 6) Аудит-логи
    await _ensure_audit_logs(conn)

    # 7) Поиск по квестам
    await _ensure_quests_search_vector(conn)

    # 8) Чистка устаревших колонок/типов
    await _drop_legacy_columns(conn)


async def _create_everything(conn, metadatas: Iterable[sa.MetaData]) -> None:
    for md in metadatas:
        # Пропускаем пустые
        if not md.tables:
            continue
        await conn.run_sync(md.create_all)


async def reset_database() -> None:
    _ensure_not_production()

    url = _normalize_pg_url(_get_database_url())
    _log(f"Подключение к БД: {url}")

    engine: AsyncEngine = create_async_engine(url, future=True, echo=False)

    try:
        is_pg = _detect_is_postgres(engine)

        async with engine.begin() as conn:
            _log("Шаг 1/3: удаляем все объекты схемы...")
            await _drop_everything(conn, is_postgres=is_pg)
            _log("Готово: схема очищена.")

            # Для Postgres дополнительно выставим search_path на целевую схему
            if is_pg:
                target_schema = _get_target_schema()
                await conn.execute(sa.text(f"SET search_path TO {sa.sql.quoted_name(target_schema, quote=True)}, public"))

            _log("Импорт моделей...")
            _import_all_models()
            metadatas = _collect_all_metadatas()
            if not metadatas:
                _log("Внимание: не найдено MetaData у моделей. Проверьте, что все модели в apps.backend.app.models импортируются.")
            else:
                _log(f"Найдено {len(metadatas)} наборов MetaData.")

            _log("Шаг 2/3: создаём таблицы из моделей...")
            await _create_everything(conn, metadatas)
            _log("Готово: базовые таблицы созданы.")

            _log("Шаг 3/3: пост-инициализация схемы...")
            await _post_create_schema_fixes(conn, is_postgres=is_pg)
            _log("Готово: схема приведена к требуемому виду.")

        _log("Финальная проверка подключения...")
        async with engine.connect() as conn:
            await conn.execute(sa.text("SELECT 1"))

        # Необязательный шаг: выравнивание состояния Alembic без выполнения миграций.
        # Укажите ALEMBIC_STAMP=head (или конкретный ревизионный id), чтобы записать версию в БД.
        # Путь к конфигу можно переопределить через ALEMBIC_CONFIG, по умолчанию 'alembic.ini'.
        stamp = os.getenv("ALEMBIC_STAMP")
        if stamp:
            try:
                from alembic import command as _al_command  # type: ignore
                from alembic.config import Config as _AlConfig  # type: ignore
                cfg_path = os.getenv("ALEMBIC_CONFIG") or "alembic.ini"
                cfg = _AlConfig(cfg_path)
                _al_command.stamp(cfg, stamp)
                _log(f"Alembic stamped to '{stamp}'.")
            except Exception as e:
                _log(f"Предупреждение: не удалось выполнить Alembic stamp: {e}")

        _log("База перезагружена и готова к работе.")

    finally:
        await engine.dispose()


def main() -> None:
    """
    Использование:
      # Dev (PostgreSQL)
      export DATABASE_URL='postgresql+asyncpg://user:pass@localhost:5432/dbname'
      python scripts/reset_db.py

      # Dev (SQLite)
      export DATABASE_URL='sqlite+aiosqlite:///./test.db'
      python scripts/reset_db.py

    Защита от production: установите FORCE_RESET=1, чтобы принудительно выполнить.
    """
    try:
        asyncio.run(reset_database())
    except Exception as e:
        _log(f"Ошибка: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
