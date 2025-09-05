"""convert account id from uuid to bigserial"""

from alembic import op
import sqlalchemy as sa

revision = "20240920_account_id_bigserial"
down_revision = "20240710_rename_workspaces_to_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS accounts_id_seq")
    op.add_column(
        "accounts",
        sa.Column(
            "id_new",
            sa.BigInteger(),
            server_default=sa.text("nextval('accounts_id_seq')"),
            nullable=False,
        ),
    )
    op.add_column(
        "account_members",
        sa.Column("account_id_new", sa.BigInteger(), nullable=True),
    )
    op.execute("UPDATE accounts SET id_new = nextval('accounts_id_seq')")
    op.execute(
        "UPDATE account_members am SET account_id_new = a.id_new FROM accounts a WHERE am.account_id = a.id"
    )
    op.drop_constraint("workspace_members_pkey", "account_members", type_="primary")
    op.drop_constraint(
        "workspace_members_workspace_id_fkey",
        "account_members",
        type_="foreignkey",
    )
    op.drop_constraint(
        "workspaces_pkey",
        "accounts",
        type_="primary",
        cascade=True,
    )
    op.drop_column("account_members", "account_id")
    op.drop_column("accounts", "id")
    op.alter_column(
        "account_members", "account_id_new", new_column_name="account_id", nullable=False
    )
    op.alter_column("accounts", "id_new", new_column_name="id", nullable=False)
    op.create_primary_key("accounts_pkey", "accounts", ["id"])
    op.create_primary_key("account_members_pkey", "account_members", ["account_id", "user_id"])
    op.create_foreign_key(None, "account_members", "accounts", ["account_id"], ["id"])


def downgrade() -> None:
    raise NotImplementedError("downgrade not supported")
