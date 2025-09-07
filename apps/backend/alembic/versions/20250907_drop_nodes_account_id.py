from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20250907_drop_nodes_account_id"
down_revision = "20250907_drop_accounts_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("nodes"):
        return

    # Drop FK on nodes.account_id if present
    fks = inspector.get_foreign_keys("nodes")
    for fk in fks:
        if (
            fk.get("referred_table") == "accounts"
            and "account_id" in (fk.get("constrained_columns") or [])
        ):
            name = fk.get("name")
            if name:
                op.drop_constraint(name, "nodes", type_="foreignkey")

    # Drop account-scoped indexes if present
    idx_names = {i["name"] for i in inspector.get_indexes("nodes")}
    for to_drop in (
        "ix_nodes_account_id_slug",
        "ix_nodes_account_id_created_at",
    ):
        if to_drop in idx_names:
            op.drop_index(to_drop, table_name="nodes")

    # Finally drop the column if it exists
    cols = {c["name"] for c in inspector.get_columns("nodes")}
    if "account_id" in cols:
        op.drop_column("nodes", "account_id")


def downgrade() -> None:  # pragma: no cover
    # Not supported (account_id removal is irreversible in this migration plan)
    pass

