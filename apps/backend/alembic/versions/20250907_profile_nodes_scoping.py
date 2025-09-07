from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20250907_profile_nodes_scoping"
down_revision = "20250212_accounts_cleanup_phase2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Allow nodes without account_id (profile-scoped)
    try:
        op.alter_column("nodes", "account_id", existing_type=sa.BigInteger(), nullable=True)
    except Exception:
        pass

    # 2) Ensure slug uniqueness per author (profile)
    try:
        op.create_index("uq_nodes_author_id_slug", "nodes", ["author_id", "slug"], unique=True)
    except Exception:
        pass

    # 3) Efficient listing of personal nodes
    try:
        op.create_index("ix_nodes_author_id_created_at", "nodes", ["author_id", "created_at"], unique=False)
    except Exception:
        pass


def downgrade() -> None:  # pragma: no cover
    # Best-effort downgrade: drop new indexes; do not force NOT NULL back if data would violate
    try:
        op.drop_index("ix_nodes_author_id_created_at", table_name="nodes")
    except Exception:
        pass
    try:
        op.drop_index("uq_nodes_author_id_slug", table_name="nodes")
    except Exception:
        pass
    # Attempt to restore NOT NULL if no NULLs present
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("nodes"):
        try:
            # Only set NOT NULL when safe
            res = bind.execute(sa.text("SELECT COUNT(*) FROM nodes WHERE account_id IS NULL"))
            nulls = int(list(res)[0][0]) if res else 0
            if nulls == 0:
                op.alter_column("nodes", "account_id", existing_type=sa.BigInteger(), nullable=False)
        except Exception:
            pass

