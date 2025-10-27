from __future__ import annotations
import os
import uuid
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from apps.backend.domains.platform.notifications.adapters.sql.notifications import (
    NotificationRepository,
)
from apps.backend.domains.platform.notifications.application.interactors.commands import (
    NotificationCreateCommand,
)


def _require_db_url() -> str:
    for key in ("NOTIFICATIONS_TEST_DATABASE_URL", "APP_DATABASE_URL", "DATABASE_URL"):
        value = os.getenv(key)
        if value:
            return value
    pytest.skip("Notifications migration test requires NOTIFICATIONS_TEST_DATABASE_URL")
    raise RuntimeError  # pragma: no cover - pytest.skip stops execution


def _to_sync_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + url[len("postgresql+asyncpg://") :]
    return url


def _to_async_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    return url


def _with_search_path(url: str, schema: str) -> str:
    parts = urlsplit(url)
    query_items = list(parse_qsl(parts.query, keep_blank_values=True))
    opts: list[str] = []
    remaining: list[tuple[str, str]] = []
    for key, value in query_items:
        if key == "options" and value:
            opts.append(value)
        else:
            remaining.append((key, value))
    opts.append(f"-csearch_path={schema}")
    remaining.append(("options", " ".join(opts)))
    query = urlencode(remaining, doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


async def _prepare_async_engine(url: str, schema: str) -> AsyncEngine:
    engine = create_async_engine(url, future=True)
    async with engine.begin() as conn:
        await conn.execute(sa.text(f"SET search_path TO {schema}"))
    return engine


@pytest.mark.asyncio
async def test_notifications_migration_round_trip() -> None:
    base_url = _require_db_url()
    schema = f"notif_migration_{uuid.uuid4().hex}"

    sync_base_url = _to_sync_url(base_url)
    async_base_url = _to_async_url(base_url)

    sync_schema_url = _with_search_path(sync_base_url, schema)
    async_schema_url = _with_search_path(async_base_url, schema)

    admin_engine = sa.create_engine(sync_base_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            conn.execute(sa.text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            conn.execute(sa.text(f"CREATE SCHEMA {schema}"))

        cfg = Config()
        cfg.set_main_option(
            "script_location",
            str(Path(__file__).resolve().parents[3] / "apps/backend/migrations"),
        )
        cfg.set_main_option("sqlalchemy.url", sync_schema_url)

        previous_url = os.environ.get("APP_DATABASE_URL")
        os.environ["APP_DATABASE_URL"] = sync_schema_url
        try:
            command.upgrade(cfg, "head")
        finally:
            if previous_url is None:
                os.environ.pop("APP_DATABASE_URL", None)
            else:
                os.environ["APP_DATABASE_URL"] = previous_url

        async_engine = await _prepare_async_engine(async_schema_url, schema)
        try:
            repo = NotificationRepository(async_engine)
            user_id = str(uuid.uuid4())
            command_payload = NotificationCreateCommand(
                user_id=user_id,
                title="Migration smoke test",
                message="Notifications schema ready",
                type_="system",
                placement="inbox",
                priority="high",
                meta={"source": "test"},
            )
            created = await repo.create_and_commit(**command_payload.to_repo_payload())
            assert created["user_id"] == user_id
            assert created["title"] == "Migration smoke test"

            items, total, unread = await repo.list_for_user(
                user_id, placement="inbox", limit=10, offset=0
            )
            assert items, "expected stored notification to be readable"
            assert items[0]["id"] == created["id"]

            marked = await repo.mark_read(user_id, created["id"])
            assert marked is not None
            assert marked["read_at"] is not None
        finally:
            await async_engine.dispose()
    finally:
        with admin_engine.connect() as conn:
            conn.execute(sa.text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
        admin_engine.dispose()
