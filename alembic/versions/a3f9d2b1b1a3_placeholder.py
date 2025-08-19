"""Placeholder migration to map existing DB revision to current chain.

Revision ID: a3f9d2b1b1a3
Revises:
Create Date: 2025-08-20 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a3f9d2b1b1a3"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # No-op: this migration exists to bridge an existing DB revision to the new chain.
    pass


def downgrade():
    # No-op downgrade
    pass
