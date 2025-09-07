from __future__ import annotations

"""Switch achievements/referrals/navigation cache to user scope.

This migration removes residual account_id/workspace_id columns and
constraints from domains that are no longer account-scoped:

- achievements: drop achievements.account_id and user_achievements.account_id
- referrals: drop workspace_id from referral_codes and referral_events
- navigation cache: drop account-scoped indexes if any remain

The migration is defensive: it checks for tables/columns/indexes/constraints
before altering so it can run safely across heterogeneous environments.
"""

import sqlalchemy as sa
from alembic import op

revision = "20250908_user_scope_cleanup"
down_revision = "20250908_remove_accounts_and_workspaces"
branch_labels = None
depends_on = None


def _drop_column(table: str, column: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table(table):
        cols = {c["name"] for c in inspector.get_columns(table)}
        if column in cols:
            try:
                op.drop_column(table, column)
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

    # Achievements: remove account linkage
    _drop_column("achievements", "account_id")
    _drop_column("user_achievements", "account_id")

    # Referrals: remove workspace linkage and related constraints
    if inspector.has_table("referral_codes"):
        _drop_constraint("referral_codes", "uq_referral_codes_ws_code", type_="unique")
        _drop_index("referral_codes", "ix_referral_codes_workspace_owner")
        _drop_index("referral_codes", "ix_referral_codes_workspace_active")
        _drop_column("referral_codes", "workspace_id")
        # Make code unique globally if not already enforced
        try:
            op.create_unique_constraint("uq_referral_codes_code", "referral_codes", ["code"])
        except Exception:
            pass

    if inspector.has_table("referral_events"):
        _drop_constraint("referral_events", "uq_referral_events_ws_referee_event", type_="unique")
        _drop_index("referral_events", "ix_referral_events_ws_referrer")
        _drop_index("referral_events", "ix_referral_events_ws_event_time")
        _drop_column("referral_events", "workspace_id")
        # Optional: narrow unique to (referee_user_id, event_type)
        try:
            op.create_unique_constraint(
                "uq_referral_events_referee_event",
                "referral_events",
                ["referee_user_id", "event_type"],
            )
        except Exception:
            pass

    # Navigation cache artefacts (if the table exists in this environment)
    if inspector.has_table("navigation_cache"):
        _drop_index("navigation_cache", "ix_navigation_cache_account_id_generated_at")
        _drop_constraint("navigation_cache", "uq_nav_cache_account_slug", type_="unique")


def downgrade() -> None:  # pragma: no cover
    # Irreversible in current migration plan
    pass

