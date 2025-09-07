from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20250211_accounts_cleanup_phase1"
down_revision = "20250210_referrals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # users: add default_account_id
    if inspector.has_table("users"):
        cols = {c["name"] for c in inspector.get_columns("users")}
        if "default_account_id" not in cols:
            op.add_column(
                "users",
                sa.Column("default_account_id", sa.BigInteger(), nullable=True),
            )
            try:
                op.create_foreign_key(None, "users", "accounts", ["default_account_id"], ["id"], ondelete=None)
            except Exception:
                pass

    # achievements: add account_id
    if inspector.has_table("achievements"):
        cols = {c["name"] for c in inspector.get_columns("achievements")}
        if "account_id" not in cols:
            op.add_column(
                "achievements",
                sa.Column("account_id", sa.BigInteger(), nullable=True),
            )
            try:
                op.create_foreign_key(None, "achievements", "accounts", ["account_id"], ["id"])
            except Exception:
                pass

    # user_achievements: add account_id
    if inspector.has_table("user_achievements"):
        cols = {c["name"] for c in inspector.get_columns("user_achievements")}
        if "account_id" not in cols:
            op.add_column(
                "user_achievements",
                sa.Column("account_id", sa.BigInteger(), nullable=True),
            )
            try:
                op.create_foreign_key(None, "user_achievements", "accounts", ["account_id"], ["id"])
            except Exception:
                pass

    # user_event_counters: add account_id
    if inspector.has_table("user_event_counters"):
        cols = {c["name"] for c in inspector.get_columns("user_event_counters")}
        if "account_id" not in cols:
            op.add_column(
                "user_event_counters",
                sa.Column("account_id", sa.BigInteger(), nullable=True),
            )
            try:
                op.create_foreign_key(None, "user_event_counters", "accounts", ["account_id"], ["id"])
            except Exception:
                pass


def downgrade() -> None:  # pragma: no cover
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("user_event_counters"):
        if any(c["name"] == "account_id" for c in inspector.get_columns("user_event_counters")):
            op.drop_column("user_event_counters", "account_id")

    if inspector.has_table("user_achievements"):
        if any(c["name"] == "account_id" for c in inspector.get_columns("user_achievements")):
            op.drop_column("user_achievements", "account_id")

    if inspector.has_table("achievements"):
        if any(c["name"] == "account_id" for c in inspector.get_columns("achievements")):
            op.drop_column("achievements", "account_id")

    if inspector.has_table("users"):
        if any(c["name"] == "default_account_id" for c in inspector.get_columns("users")):
            op.drop_column("users", "default_account_id")

