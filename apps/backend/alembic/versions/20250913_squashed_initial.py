"""Squashed initial schema

Revision ID: 20250913_squashed_initial
Revises: None
Create Date: 2025-09-13

This migration squashes prior revisions into a single baseline that
creates the current schema as defined by SQLAlchemy models.

For existing databases already on the previous head, use:

    alembic stamp 20250913_squashed_initial

For new databases, run the usual:

    alembic upgrade head
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250913_squashed_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create all tables/indexes defined in current models.
    # Import inside function so Alembic's env.py sys.path changes apply.
    from app.providers.db.base import Base  # noqa

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:  # pragma: no cover
    # Destructive downgrade is not supported for the squashed baseline.
    raise NotImplementedError("downgrade not supported for squashed baseline")

