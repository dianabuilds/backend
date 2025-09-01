"""migrate content_items and node_patches ids to bigint

Revision ID: 20260115_content_items_bigint_ids
Revises: 20260101_node_tags_node_id_bigint
Create Date: 2025-01-15 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260115_content_items_bigint_ids"
down_revision = "20260101_node_tags_node_id_bigint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # content_items.id_bigint
    op.add_column(
        "content_items", sa.Column("id_bigint", sa.BigInteger(), nullable=True)
    )
    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS content_items_id_bigint_seq OWNED BY content_items.id_bigint"
    )
    op.execute(
        "ALTER TABLE content_items ALTER COLUMN id_bigint SET DEFAULT nextval('content_items_id_bigint_seq')"
    )
    op.execute(
        "UPDATE content_items SET id_bigint = nextval('content_items_id_bigint_seq')"
    )
    op.alter_column("content_items", "id_bigint", nullable=False)

    # prepare referencing tables with bigint columns
    op.add_column(
        "node_patches", sa.Column("node_id_bigint", sa.BigInteger(), nullable=True)
    )
    op.execute(
        """
        UPDATE node_patches np
        SET node_id_bigint = ci.id_bigint
        FROM content_items ci
        WHERE np.node_id = ci.id
        """
    )
    op.alter_column("node_patches", "node_id_bigint", nullable=False)

    op.add_column(
        "content_tags", sa.Column("content_id_bigint", sa.BigInteger(), nullable=True)
    )
    op.execute(
        """
        UPDATE content_tags ct
        SET content_id_bigint = ci.id_bigint
        FROM content_items ci
        WHERE ct.content_id = ci.id
        """
    )
    op.alter_column("content_tags", "content_id_bigint", nullable=False)

    # drop old foreign keys and indexes referencing content_items.id
    op.drop_constraint(
        "content_patches_content_id_fkey", "node_patches", type_="foreignkey"
    )
    op.drop_index("ix_node_patches_node_id", table_name="node_patches")
    op.drop_constraint(
        "content_tags_content_id_fkey", "content_tags", type_="foreignkey"
    )
    op.drop_index("ix_content_tags_content_id", table_name="content_tags")

    # switch content_items primary key
    op.drop_constraint("content_items_pkey", "content_items", type_="primary")
    op.create_primary_key("content_items_pkey", "content_items", ["id_bigint"])

    # node_patches.id_bigint and primary key
    op.add_column(
        "node_patches", sa.Column("id_bigint", sa.BigInteger(), nullable=True)
    )
    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS node_patches_id_bigint_seq OWNED BY node_patches.id_bigint"
    )
    op.execute(
        "ALTER TABLE node_patches ALTER COLUMN id_bigint SET DEFAULT nextval('node_patches_id_bigint_seq')"
    )
    op.execute(
        "UPDATE node_patches SET id_bigint = nextval('node_patches_id_bigint_seq')"
    )
    op.alter_column("node_patches", "id_bigint", nullable=False)
    op.drop_constraint("content_patches_pkey", "node_patches", type_="primary")
    op.create_primary_key("node_patches_pkey", "node_patches", ["id_bigint"])

    # recreate foreign keys and indexes to bigint columns
    op.create_foreign_key(
        "node_patches_node_id_bigint_fkey",
        "node_patches",
        "content_items",
        ["node_id_bigint"],
        ["id_bigint"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_node_patches_node_id_bigint", "node_patches", ["node_id_bigint"]
    )

    op.create_foreign_key(
        "content_tags_content_id_bigint_fkey",
        "content_tags",
        "content_items",
        ["content_id_bigint"],
        ["id_bigint"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_content_tags_content_id_bigint",
        "content_tags",
        ["content_id_bigint"],
    )

    # drop old uuid columns
    op.drop_column("node_patches", "node_id")
    op.drop_column("node_patches", "id")
    op.drop_column("content_tags", "content_id")
    op.drop_column("content_items", "id")


def downgrade() -> None:
    op.add_column(
        "content_items",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute("UPDATE content_items SET id = gen_random_uuid()")
    op.alter_column("content_items", "id", nullable=False)
    op.drop_constraint("content_items_pkey", "content_items", type_="primary")
    op.create_primary_key("content_items_pkey", "content_items", ["id"])

    op.add_column(
        "node_patches",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "node_patches",
        sa.Column("node_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute("UPDATE node_patches SET id = gen_random_uuid()")
    op.execute(
        """
        UPDATE node_patches np
        SET node_id = ci.id
        FROM content_items ci
        WHERE np.node_id_bigint = ci.id_bigint
        """
    )
    op.alter_column("node_patches", "id", nullable=False)
    op.alter_column("node_patches", "node_id", nullable=False)
    op.drop_constraint("node_patches_pkey", "node_patches", type_="primary")
    op.create_primary_key("node_patches_pkey", "node_patches", ["id"])
    op.drop_constraint(
        "node_patches_node_id_bigint_fkey", "node_patches", type_="foreignkey"
    )
    op.drop_index("ix_node_patches_node_id_bigint", table_name="node_patches")
    op.create_foreign_key(
        "content_patches_content_id_fkey",
        "node_patches",
        "content_items",
        ["node_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_node_patches_node_id", "node_patches", ["node_id"])

    # content_tags.content_id back to uuid
    op.add_column(
        "content_tags",
        sa.Column(
            "content_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True
        ),
    )
    op.execute(
        """
        UPDATE content_tags ct
        SET content_id = ci.id
        FROM content_items ci
        WHERE ct.content_id_bigint = ci.id_bigint
        """
    )
    op.alter_column("content_tags", "content_id", nullable=False)
    op.drop_constraint(
        "content_tags_content_id_bigint_fkey", "content_tags", type_="foreignkey"
    )
    op.drop_index("ix_content_tags_content_id_bigint", table_name="content_tags")
    op.create_foreign_key(
        "content_tags_content_id_fkey",
        "content_tags",
        "content_items",
        ["content_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_content_tags_content_id", "content_tags", ["content_id"])

    op.drop_column("content_tags", "content_id_bigint")
    op.drop_column("node_patches", "node_id_bigint")
    op.drop_column("node_patches", "id_bigint")
    op.drop_column("content_items", "id_bigint")
