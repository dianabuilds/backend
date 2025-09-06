from alembic import op
import sqlalchemy as sa

revision = "20241210_slug_scoped_by_workspace"
down_revision = "20241206_transition_fk_ondelete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("nodes_slug_key", "nodes", type_="unique")
    op.create_index(
        "ix_nodes_account_id_slug",
        "nodes",
        ["account_id", "slug"],
        unique=True,
    )
    op.create_index(
        "ix_nodes_account_id_created_at",
        "nodes",
        ["account_id", "created_at"],
    )

    op.drop_constraint("content_items_slug_key", "content_items", type_="unique")
    op.create_index(
        "ix_content_items_workspace_id_slug",
        "content_items",
        ["workspace_id", "slug"],
        unique=True,
    )
    op.create_index(
        "ix_content_items_workspace_id_created_at",
        "content_items",
        ["workspace_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_content_items_workspace_id_created_at",
        table_name="content_items",
    )
    op.drop_index(
        "ix_content_items_workspace_id_slug",
        table_name="content_items",
    )
    op.create_unique_constraint(
        "content_items_slug_key",
        "content_items",
        ["slug"],
    )

    op.drop_index(
        "ix_nodes_account_id_created_at",
        table_name="nodes",
    )
    op.drop_index(
        "ix_nodes_account_id_slug",
        table_name="nodes",
    )
    op.create_unique_constraint(
        "nodes_slug_key",
        "nodes",
        ["slug"],
    )
