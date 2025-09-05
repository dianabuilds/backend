from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20241020_nodes_account_id_bigint"
down_revision = "20241015_user_default_workspace"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("nodes", sa.Column("account_id_int", sa.BigInteger(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE nodes AS n
            SET account_id_int = a.id
            FROM accounts AS a
            WHERE n.account_id::text = a.id::text
            """
        )
    )
    op.drop_constraint("nodes_account_id_fkey", "nodes", type_="foreignkey")
    op.drop_column("nodes", "account_id")
    op.alter_column("nodes", "account_id_int", new_column_name="account_id", nullable=False)
    op.create_foreign_key(None, "nodes", "accounts", ["account_id"], ["id"])


def downgrade() -> None:  # pragma: no cover
    raise NotImplementedError("downgrade not supported")
