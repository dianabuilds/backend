from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20250907_drop_accounts_domain"
down_revision = "20250907_profile_nodes_scoping"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Safe phase-1 cleanup of accounts domain.

    Important: Do NOT drop tables that may still be referenced by FKs in this
    phase to avoid aborting the transaction. Only remove columns that are
    guaranteed to be safe and leave destructive drops for a dedicated phase
    after dependents are cleaned (e.g. dropping nodes.account_id).
    """

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # users.default_account_id — drop FK then column if present
    if inspector.has_table("users"):
        cols = {c["name"] for c in inspector.get_columns("users")}
        if "default_account_id" in cols:
            # Drop FK that references accounts, if any
            fks = inspector.get_foreign_keys("users")
            for fk in fks:
                if (
                    "constrained_columns" in fk
                    and "referred_table" in fk
                    and fk.get("referred_table") == "accounts"
                    and "default_account_id" in (fk.get("constrained_columns") or [])
                ):
                    # Constraint name is required for drop_constraint
                    name = fk.get("name")
                    if name:
                        op.drop_constraint(name, "users", type_="foreignkey")
            op.drop_column("users", "default_account_id")

    # Note: We deliberately DO NOT drop account_members/accounts or related enums
    # in this migration because other tables (e.g. nodes.account_id, achievements)
    # may still reference them. A later migration will:
    #  1) drop all referencing FKs/columns
    #  2) drop account_members/accounts tables
    #  3) drop account_kind/account_role types


def downgrade() -> None:  # pragma: no cover
    # Non-trivial; re-creating whole accounts domain is out of scope.
    pass
