from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20250212_accounts_cleanup_phase2"
down_revision = "20250211_accounts_cleanup_phase1"
branch_labels = None
depends_on = None


def _has_column(inspector: sa.Inspector, table: str, column: str) -> bool:
    return any(c["name"] == column for c in inspector.get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Fill users.default_account_id from ownership first, then any membership
    if inspector.has_table("users") and inspector.has_table("account_members") and _has_column(
        inspector, "users", "default_account_id"
    ):
        try:
            op.execute(
                sa.text(
                    """
                    UPDATE users AS u
                    SET default_account_id = am.account_id
                    FROM account_members AS am
                    WHERE am.user_id = u.id AND u.default_account_id IS NULL AND am.role = 'owner'
                    """
                )
            )
        except Exception:
            pass
        try:
            op.execute(
                sa.text(
                    """
                    UPDATE users AS u
                    SET default_account_id = am.account_id
                    FROM account_members AS am
                    WHERE am.user_id = u.id AND u.default_account_id IS NULL
                    """
                )
            )
        except Exception:
            pass

    # Helper subquery: pick a system account if exists
    system_account_id_sql = "SELECT id FROM accounts WHERE is_system = TRUE ORDER BY id LIMIT 1"

    # Migrate user_achievements.account_id from users.default_account_id
    if inspector.has_table("user_achievements") and _has_column(
        inspector, "user_achievements", "account_id"
    ):
        try:
            op.execute(
                sa.text(
                    """
                    UPDATE user_achievements AS ua
                    SET account_id = u.default_account_id
                    FROM users AS u
                    WHERE ua.user_id = u.id AND ua.account_id IS NULL
                    """
                )
            )
        except Exception:
            pass

    # Migrate user_event_counters.account_id from users.default_account_id
    if inspector.has_table("user_event_counters") and _has_column(
        inspector, "user_event_counters", "account_id"
    ):
        try:
            op.execute(
                sa.text(
                    """
                    UPDATE user_event_counters AS c
                    SET account_id = u.default_account_id
                    FROM users AS u
                    WHERE c.user_id = u.id AND c.account_id IS NULL
                    """
                )
            )
        except Exception:
            pass

    # Achievements: if account_id is NULL, set to system account if available
    if inspector.has_table("achievements") and _has_column(inspector, "achievements", "account_id"):
        try:
            op.execute(sa.text(f"UPDATE achievements SET account_id = ({system_account_id_sql}) WHERE account_id IS NULL"))
        except Exception:
            pass

    # Drop legacy workspace_id columns when present
    if inspector.has_table("user_event_counters") and _has_column(
        inspector, "user_event_counters", "workspace_id"
    ):
        op.drop_column("user_event_counters", "workspace_id")

    if inspector.has_table("user_achievements") and _has_column(
        inspector, "user_achievements", "workspace_id"
    ):
        op.drop_column("user_achievements", "workspace_id")

    if inspector.has_table("achievements") and _has_column(inspector, "achievements", "workspace_id"):
        op.drop_column("achievements", "workspace_id")


def downgrade() -> None:  # pragma: no cover
    # Downgrade is not supported for destructive cleanup
    pass

