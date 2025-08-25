"""ensure tags.workspace_id exists and is indexed"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "20251212_add_workspace_id_to_tags"
down_revision = "20251211_add_workspace_id_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table = "tags"
    if table in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns(table)}
        if "workspace_id" not in cols:
            op.add_column(
                table,
                sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(
                "fk_tags_workspace_id", table, "workspaces", ["workspace_id"], ["id"]
            )
            op.execute(
                sa.text(
                    "UPDATE tags SET workspace_id = (SELECT id FROM workspaces WHERE slug='main' LIMIT 1)"
                )
            )
            op.alter_column(table, "workspace_id", nullable=False)
        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        if "ix_tags_workspace_id" not in indexes:
            op.create_index("ix_tags_workspace_id", table, ["workspace_id"])
        constraints = {c["name"] for c in inspector.get_unique_constraints(table)}
        if "uq_tags_slug" in constraints:
            op.drop_constraint("uq_tags_slug", table_name=table, type_="unique")
        if "uq_tags_workspace_slug" not in constraints:
            op.create_unique_constraint("uq_tags_workspace_slug", table, ["workspace_id", "slug"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table = "tags"
    if table in inspector.get_table_names():
        constraints = {c["name"] for c in inspector.get_unique_constraints(table)}
        if "uq_tags_workspace_slug" in constraints:
            op.drop_constraint("uq_tags_workspace_slug", table_name=table, type_="unique")
        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        if "ix_tags_workspace_id" in indexes:
            op.drop_index("ix_tags_workspace_id", table_name=table)
        fks = {fk["name"] for fk in inspector.get_foreign_keys(table)}
        if "fk_tags_workspace_id" in fks:
            op.drop_constraint("fk_tags_workspace_id", table_name=table, type_="foreignkey")
        cols = {c["name"] for c in inspector.get_columns(table)}
        if "workspace_id" in cols:
            op.drop_column(table, "workspace_id")
