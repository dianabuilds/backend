"""Seed default global header block for site editor.

Revision ID: 0113_site_global_header_seed
Revises: 0112_site_editor_homepage_bootstrap
Create Date: 2025-10-27
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0113_site_global_header_seed"
down_revision = "0112_site_editor_homepage_bootstrap"
branch_labels = None
depends_on = None

METADATA = sa.MetaData()

STATUS_ENUM = pg.ENUM(
    "draft",
    "published",
    "archived",
    name="site_global_block_status",
    create_type=False,
)

REVIEW_STATUS_ENUM = pg.ENUM(
    "none",
    "pending",
    "approved",
    "rejected",
    name="site_page_review_status",
    create_type=False,
)

SITE_GLOBAL_BLOCKS_TABLE = sa.Table(
    "site_global_blocks",
    METADATA,
    sa.Column("id", pg.UUID(as_uuid=True)),
    sa.Column("key", sa.Text()),
    sa.Column("title", sa.Text()),
    sa.Column("section", sa.Text()),
    sa.Column("locale", sa.Text()),
    sa.Column("status", STATUS_ENUM),
    sa.Column("review_status", REVIEW_STATUS_ENUM),
    sa.Column("data", pg.JSONB(astext_type=sa.Text())),
    sa.Column("meta", pg.JSONB(astext_type=sa.Text())),
    sa.Column("updated_at", sa.DateTime(timezone=True)),
    sa.Column("updated_by", sa.Text()),
    sa.Column("published_version", sa.BigInteger()),
    sa.Column("draft_version", sa.BigInteger()),
    sa.Column("requires_publisher", sa.Boolean()),
    sa.Column("comment", sa.Text()),
    sa.Column("usage_count", sa.BigInteger()),
)

SITE_AUDIT_LOG_TABLE = sa.Table(
    "site_audit_log",
    METADATA,
    sa.Column("id", pg.UUID(as_uuid=True)),
    sa.Column("entity_type", sa.Text()),
    sa.Column("entity_id", pg.UUID(as_uuid=True)),
    sa.Column("action", sa.Text()),
    sa.Column("snapshot", pg.JSONB(astext_type=sa.Text())),
    sa.Column("actor", sa.Text()),
    sa.Column("created_at", sa.DateTime(timezone=True)),
)

BLOCK_KEY = "header-default"


def _default_header_data() -> dict[str, Any]:
    return {
        "branding": {
            "title": "Caves World",
            "subtitle": "Играй и создавай",
            "href": "/",
            "logo": {
                "light": "/assets/branding/logo-light.svg",
                "dark": "/assets/branding/logo-dark.svg",
                "alt": "Caves World",
            },
        },
        "navigation": {
            "primary": [
                {"id": "home", "label": "Главная", "href": "/"},
                {"id": "quests", "label": "Квесты", "href": "/quests"},
                {"id": "dev-blog", "label": "Dev Blog", "href": "/dev-blog"},
                {"id": "pricing", "label": "Тарифы", "href": "/pricing"},
            ],
            "utility": [
                {"id": "help", "label": "Помощь", "href": "/help"},
                {"id": "blog", "label": "Блог", "href": "/dev-blog"},
            ],
            "cta": {
                "id": "signup",
                "label": "Присоединиться",
                "href": "/auth/signup",
                "style": "primary",
            },
            "mobile": {
                "menu": [
                    {"id": "home", "label": "Главная", "href": "/"},
                    {"id": "quests", "label": "Квесты", "href": "/quests"},
                    {"id": "dev-blog", "label": "Dev Blog", "href": "/dev-blog"},
                    {"id": "pricing", "label": "Тарифы", "href": "/pricing"},
                    {"id": "help", "label": "Помощь", "href": "/help"},
                ],
                "cta": {
                    "id": "signup",
                    "label": "Присоединиться",
                    "href": "/auth/signup",
                    "style": "primary",
                },
            },
        },
        "layout": {"variant": "default", "sticky": True},
        "features": {"language_switcher": True},
        "localization": {"fallbackLocale": "ru", "available": ["ru", "en"]},
    }


def _default_header_meta() -> dict[str, Any]:
    return {
        "owner": "team_public_site",
        "documentation": "/docs/site-editor-block-library#global_header",
        "seed": True,
    }


def upgrade() -> None:
    bind = op.get_bind()
    if bind is None:
        raise RuntimeError("Alembic connection is unavailable")

    inspector = sa.inspect(bind)
    if not inspector.has_table("site_global_blocks"):
        return

    conn = bind
    existing_block = conn.execute(
        sa.select(SITE_GLOBAL_BLOCKS_TABLE.c.id).where(
            SITE_GLOBAL_BLOCKS_TABLE.c.key == BLOCK_KEY
        )
    ).scalar_one_or_none()
    if existing_block is not None:
        return

    now = datetime.now(UTC)
    actor = "seed:site-editor"
    block_id = uuid.uuid4()

    conn.execute(
        SITE_GLOBAL_BLOCKS_TABLE.insert().values(
            id=block_id,
            key=BLOCK_KEY,
            title="Глобальный хедер",
            section="header",
            locale="ru",
            status="draft",
            review_status="none",
            data=_default_header_data(),
            meta=_default_header_meta(),
            updated_at=now,
            updated_by=actor,
            published_version=None,
            draft_version=1,
            requires_publisher=True,
            comment="Seed: default header navigation",
            usage_count=0,
        )
    )

    if inspector.has_table("site_audit_log"):
        conn.execute(
            SITE_AUDIT_LOG_TABLE.insert().values(
                id=uuid.uuid4(),
                entity_type="global_block",
                entity_id=block_id,
                action="create",
                snapshot={"key": BLOCK_KEY, "section": "header", "seed": True},
                actor=actor,
                created_at=now,
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind is None:
        raise RuntimeError("Alembic connection is unavailable")

    inspector = sa.inspect(bind)
    if not inspector.has_table("site_global_blocks"):
        return

    conn = bind
    block_id = conn.execute(
        sa.select(SITE_GLOBAL_BLOCKS_TABLE.c.id).where(
            SITE_GLOBAL_BLOCKS_TABLE.c.key == BLOCK_KEY
        )
    ).scalar_one_or_none()
    if block_id is None:
        return

    if inspector.has_table("site_audit_log"):
        conn.execute(
            SITE_AUDIT_LOG_TABLE.delete().where(
                sa.and_(
                    SITE_AUDIT_LOG_TABLE.c.entity_type == "global_block",
                    SITE_AUDIT_LOG_TABLE.c.entity_id == block_id,
                    SITE_AUDIT_LOG_TABLE.c.action == "create",
                    SITE_AUDIT_LOG_TABLE.c.actor == "seed:site-editor",
                )
            )
        )

    conn.execute(
        SITE_GLOBAL_BLOCKS_TABLE.delete().where(
            SITE_GLOBAL_BLOCKS_TABLE.c.id == block_id
        )
    )
