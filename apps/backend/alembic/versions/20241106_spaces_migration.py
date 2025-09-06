from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision = "20241106_spaces_migration"
down_revision = "20241026_audit_log_override_reason"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "spaces",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("owner_id", UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("settings", JSONB, nullable=False, server_default=sa.text("'{}'")),
    )
    op.create_table(
        "space_members",
        sa.Column(
            "space_id",
            sa.BigInteger(),
            sa.ForeignKey("spaces.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("role", sa.String(), nullable=False),
    )

    op.add_column("nodes", sa.Column("space_id", sa.BigInteger(), nullable=True))
    op.execute(sa.text("UPDATE nodes SET space_id = account_id"))
    op.create_foreign_key("fk_nodes_space_id_spaces", "nodes", "spaces", ["space_id"], ["id"])
    op.execute("ALTER TABLE nodes DROP CONSTRAINT IF EXISTS nodes_slug_key")
    op.create_index("ix_nodes_space_id_slug", "nodes", ["space_id", "slug"], unique=True)
    op.create_index("ix_nodes_space_id_created_at", "nodes", ["space_id", "created_at"])

    op.add_column("node_transitions", sa.Column("space_id", sa.BigInteger(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE node_transitions AS nt
            SET space_id = n.account_id
            FROM nodes AS n
            WHERE nt.from_node_id = n.id
            """
        )
    )
    op.create_foreign_key(
        "fk_node_transitions_space_id_spaces",
        "node_transitions",
        "spaces",
        ["space_id"],
        ["id"],
    )
    op.create_index(
        "ix_node_transitions_space_id_created_at",
        "node_transitions",
        ["space_id", "created_at"],
    )

    op.add_column("navigation_cache", sa.Column("space_id", sa.BigInteger(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE navigation_cache AS nc
            SET space_id = n.account_id
            FROM nodes AS n
            WHERE nc.node_slug = n.slug
            """
        )
    )
    op.create_foreign_key(
        "fk_navigation_cache_space_id_spaces",
        "navigation_cache",
        "spaces",
        ["space_id"],
        ["id"],
    )
    op.execute(
        "ALTER TABLE navigation_cache DROP CONSTRAINT IF EXISTS navigation_cache_node_slug_key"
    )
    op.create_unique_constraint(
        "uq_nav_cache_space_slug",
        "navigation_cache",
        ["space_id", "node_slug"],
    )
    op.create_index(
        "ix_navigation_cache_space_id_generated_at",
        "navigation_cache",
        ["space_id", "generated_at"],
    )

    op.execute(
        sa.text(
            """
            INSERT INTO spaces (id, type, owner_id, title, settings)
            SELECT id, type::text, owner_user_id, name, settings_json FROM accounts
            """
        )
    )
    op.execute("SELECT setval('spaces_id_seq', (SELECT COALESCE(MAX(id),0) FROM spaces))")
    op.execute(
        sa.text(
            """
            INSERT INTO space_members (space_id, user_id, role)
            SELECT account_id, user_id, role::text FROM account_members
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_navigation_cache_space_id_generated_at", table_name="navigation_cache")
    op.drop_constraint("uq_nav_cache_space_slug", "navigation_cache", type_="unique")
    op.create_unique_constraint("navigation_cache_node_slug_key", "navigation_cache", ["node_slug"])
    op.drop_constraint(
        "fk_navigation_cache_space_id_spaces", "navigation_cache", type_="foreignkey"
    )
    op.drop_column("navigation_cache", "space_id")

    op.drop_index("ix_node_transitions_space_id_created_at", table_name="node_transitions")
    op.drop_constraint(
        "fk_node_transitions_space_id_spaces", "node_transitions", type_="foreignkey"
    )
    op.drop_column("node_transitions", "space_id")

    op.drop_index("ix_nodes_space_id_created_at", table_name="nodes")
    op.drop_index("ix_nodes_space_id_slug", table_name="nodes")
    op.execute("ALTER TABLE nodes ADD CONSTRAINT nodes_slug_key UNIQUE (slug)")
    op.drop_constraint("fk_nodes_space_id_spaces", "nodes", type_="foreignkey")
    op.drop_column("nodes", "space_id")

    op.drop_table("space_members")
    op.drop_table("spaces")
