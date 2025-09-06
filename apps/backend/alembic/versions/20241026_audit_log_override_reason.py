from alembic import op
import sqlalchemy as sa

revision = "20241026_audit_log_override_reason"
down_revision = "20241020_nodes_account_id_bigint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column("override", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("audit_logs", sa.Column("reason", sa.String(), nullable=True))
    op.alter_column("audit_logs", "override", server_default=None)


def downgrade() -> None:  # pragma: no cover
    op.drop_column("audit_logs", "reason")
    op.drop_column("audit_logs", "override")
