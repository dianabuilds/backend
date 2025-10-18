from __future__ import annotations
import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text

from packages.core.config import load_settings, to_async_dsn
from packages.core.db import get_async_engine

from tests.conftest import add_auth, make_jwt

_ADMIN_SECRET = load_settings().admin_api_key
ADMIN_KEY = _ADMIN_SECRET.get_secret_value() if _ADMIN_SECRET else ""
if not ADMIN_KEY:
    pytest.skip(
        "APP_ADMIN_API_KEY is required for admin endpoints", allow_module_level=True
    )


def test_moderation_list_create_add_note(app_client):
    # Admin key required; also CSRF cookie/header handled by conftest add_auth
    uid = str(uuid4())
    tok = make_jwt(uid, role="admin")
    add_auth(app_client, tok)
    headers = {"X-Admin-Key": ADMIN_KEY}

    # Initially list empty
    r0 = app_client.get("/v1/moderation/cases", headers=headers)
    assert r0.status_code == 200, r0.text

    # Create case
    c = app_client.post(
        "/v1/moderation/cases", json={"title": "t", "description": "d"}, headers=headers
    )
    assert c.status_code == 200, c.text
    cid = c.json()["id"]

    # Add note
    n = app_client.post(
        f"/v1/moderation/cases/{cid}/notes", json={"text": "ping"}, headers=headers
    )
    assert n.status_code == 200, n.text
    assert n.json()["text"] == "ping"


def test_moderation_users_notes_persisted(app_client):
    uid = str(uuid4())
    tok = make_jwt(uid, role="admin")
    add_auth(app_client, tok)
    headers = {"X-Admin-Key": ADMIN_KEY}

    container = app_client.app.state.container
    dsn = to_async_dsn(container.settings.database_url)
    assert dsn, "Database DSN is required for moderation user notes test"
    engine = get_async_engine(
        "test-moderation-users-notes", url=dsn, future=True, cache=False
    )
    loop = asyncio.get_event_loop()

    test_user_id = str(uuid4())
    username = f"mod-notes-{test_user_id[:8]}"
    email = f"{test_user_id[:8]}@example.com"

    async def setup() -> None:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            await conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS moderator_user_notes (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    text text NOT NULL,
                    author_id text NULL,
                    author_name text NULL,
                    meta jsonb NOT NULL DEFAULT '{}'::jsonb,
                    pinned boolean NOT NULL DEFAULT false,
                    created_at timestamptz NOT NULL DEFAULT now()
                )
                """
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_moderator_user_notes_user ON moderator_user_notes (user_id, pinned, created_at)"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_moderator_user_notes_created_at ON moderator_user_notes (created_at)"
                )
            )
            await conn.execute(
                text(
                    "INSERT INTO users (id, email, username) VALUES (cast(:id as uuid), :email, :username)"
                ),
                {"id": test_user_id, "email": email, "username": username},
            )

    loop.run_until_complete(setup())

    payload = {
        "text": "Persistent moderator note",
        "pinned": True,
        "author_id": "moderator:test",
        "author_name": "Test Moderator",
    }

    try:
        response = app_client.post(
            f"/api/moderation/users/{test_user_id}/notes",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 200, response.text
        note = response.json()
        assert note["text"] == payload["text"]
        assert note["pinned"] is True

        detail = app_client.get(
            f"/api/moderation/users/{test_user_id}", headers=headers
        )
        assert detail.status_code == 200, detail.text
        data = detail.json()
        assert data["notes_count"] == 1
        assert data["notes"]
        assert data["notes"][0]["text"] == payload["text"]
        assert data["notes"][0]["pinned"] is True
    finally:

        async def cleanup() -> None:
            async with engine.begin() as conn:
                await conn.execute(
                    text(
                        "DELETE FROM moderator_user_notes WHERE user_id = cast(:id as uuid)"
                    ),
                    {"id": test_user_id},
                )
                await conn.execute(
                    text("DELETE FROM users WHERE id = cast(:id as uuid)"),
                    {"id": test_user_id},
                )
            await engine.dispose()

        loop.run_until_complete(cleanup())
