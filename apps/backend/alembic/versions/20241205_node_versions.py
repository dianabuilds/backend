from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20241205_node_versions"
down_revision = "20241106_spaces_migration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("node_versions"):
        return

    op.create_table(
        "node_versions",
        sa.Column("node_id", sa.BigInteger(), sa.ForeignKey("nodes.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("meta", JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.PrimaryKeyConstraint("node_id", "version"),
    )


def downgrade() -> None:  # pragma: no cover
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("node_versions"):
        op.drop_table("node_versions")
