"""
Create product tables for nodes, quests, and tags

Revision ID: 0002
Revises: 0001
Create Date: 2025-09-15

"""

from __future__ import annotations

from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def upgrade() -> None:
    base = Path(__file__).resolve().parents[2]  # apps/apps/backend
    files = [
        # Nodes
        base / "domains" / "product" / "nodes" / "schema" / "sql" / "001_nodes.sql",
        base / "domains" / "product" / "nodes" / "schema" / "sql" / "002_node_tags.sql",
        # Quests
        base / "domains" / "product" / "quests" / "schema" / "sql" / "001_quests.sql",
        base / "domains" / "product" / "quests" / "schema" / "sql" / "002_quest_tags.sql",
        # Worlds
        base / "domains" / "product" / "worlds" / "schema" / "sql" / "001_worlds.sql",
        base / "domains" / "product" / "worlds" / "schema" / "sql" / "002_characters.sql",
        # Moderation
        base / "domains" / "product" / "moderation" / "schema" / "sql" / "001_cases.sql",
        base / "domains" / "product" / "moderation" / "schema" / "sql" / "002_notes.sql",
        # Referrals
        base / "domains" / "product" / "referrals" / "schema" / "sql" / "001_codes.sql",
        base / "domains" / "product" / "referrals" / "schema" / "sql" / "002_events.sql",
        # Tags
        base / "domains" / "product" / "tags" / "schema" / "sql" / "001_tags.sql",
        base / "domains" / "product" / "tags" / "schema" / "sql" / "002_tag_aliases.sql",
        base / "domains" / "product" / "tags" / "schema" / "sql" / "003_tag_blacklist.sql",
        base / "domains" / "product" / "tags" / "schema" / "sql" / "004_tag_usage_counters.sql",
    ]
    for f in files:
        sql = _read_sql(f)
        if sql.strip():
            op.execute(sql)


def downgrade() -> None:
    # Drop in reverse dependency order
    drops = [
        "DROP TABLE IF EXISTS product_quest_tags CASCADE",
        "DROP TABLE IF EXISTS product_quests CASCADE",
        "DROP TABLE IF EXISTS product_node_tags CASCADE",
        "DROP TABLE IF EXISTS product_nodes CASCADE",
        "DROP TABLE IF EXISTS product_tag_usage_counters CASCADE",
        "DROP TABLE IF EXISTS product_tag_alias CASCADE",
        "DROP TABLE IF EXISTS product_tag_blacklist CASCADE",
        "DROP TABLE IF EXISTS product_tag CASCADE",
    ]
    for stmt in drops:
        op.execute(stmt)
