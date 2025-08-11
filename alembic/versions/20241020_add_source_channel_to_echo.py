from alembic import op
import sqlalchemy as sa

revision = '20241020_add_source_channel_to_echo'
down_revision = '20241001_add_idempotency_and_outbox'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('echo_trace', sa.Column('source', sa.String(), nullable=True))
    op.add_column('echo_trace', sa.Column('channel', sa.String(), nullable=True))


def downgrade():
    op.drop_column('echo_trace', 'channel')
    op.drop_column('echo_trace', 'source')
