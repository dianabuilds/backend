from __future__ import annotations

"""Remove residual accounts/workspaces artifacts (Phase B).

This migration performs a safe cleanup of the legacy accounts/workspaces
infrastructure:

- Drops foreign key constraints that still reference "accounts".
- Drops per-account indexes/constraints left on helper tables.
- Drops the tables "account_members" and "accounts" when present.
- Drops legacy enum types (account_kind/account_role) when present.
- Drops the "workspaces" table if it still exists (FKs to workspaces were
  removed in an earlier migration).

Columns that previously referenced accounts remain as plain nullable columns
so that dependent domains (achievements/referrals/navigation cache) can be
cleaned up incrementally without breaking reads. Subsequent migrations may
drop or repurpose those columns entirely.
"""

import sqlalchemy as sa
from alembic import op

revision = "20250908_remove_accounts_and_workspaces"
down_revision = "20250907_drop_nodes_account_id"
branch_labels = None
depends_on = None


def _drop_fk_constraints_referencing(table: str, referred_table: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table):
        return
    for fk in inspector.get_foreign_keys(table):
        if fk.get("referred_table") == referred_table:
            name = fk.get("name")
            if name:
                try:
                    op.drop_constraint(name, table, type_="foreignkey")
                except Exception:
                    pass


def _drop_index(table: str, name: str) -> None:
    try:
        op.drop_index(name, table_name=table)
    except Exception:
        pass


def _drop_constraint(table: str, name: str, type_: str) -> None:
    try:
        op.drop_constraint(name, table, type_=type_)
    except Exception:
        pass


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1) Drop FKs that still reference "accounts"
    for tbl in [
        "node_transitions",
        "navigation_cache",
        "achievements",
        "user_achievements",
        "user_event_counters",
        "referral_codes",
        "referral_events",
        "referral_rewards",
        "users",
    ]:
        _drop_fk_constraints_referencing(tbl, "accounts")

    # navigation_cache per-account artefacts
    if inspector.has_table("navigation_cache"):
        _drop_index("navigation_cache", "ix_navigation_cache_account_id_generated_at")
        _drop_constraint("navigation_cache", "uq_nav_cache_account_slug", type_="unique")

    # node_transitions per-account artefacts
    if inspector.has_table("node_transitions"):
        _drop_index("node_transitions", "ix_node_transitions_account_id_created_at")

    # 2) Drop account tables (account_members first)
    for tbl in ["account_members", "accounts"]:
        try:
            if inspector.has_table(tbl):
                op.drop_table(tbl)
        except Exception:
            # Ignore if already dropped in another branch/migration
            pass

    # 3) Drop related enum types if they exist (PostgreSQL)
    try:
        op.execute(sa.text("DROP TYPE IF EXISTS account_kind CASCADE"))
    except Exception:
        pass
    try:
        op.execute(sa.text("DROP TYPE IF EXISTS account_role CASCADE"))
    except Exception:
        pass

    # 4) Drop workspaces table (FKs were already removed earlier)
    try:
        if inspector.has_table("workspaces"):
            op.drop_table("workspaces")
    except Exception:
        pass


def downgrade() -> None:  # pragma: no cover
    # Irreversible destructive cleanup
    pass

