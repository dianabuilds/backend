from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241001_add_idempotency_and_outbox'
down_revision = '20240915_add_event_quests'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'idempotency_keys',
        sa.Column('key', sa.String(), primary_key=True),
        sa.Column('fingerprint', sa.String(), nullable=False),
        sa.Column('status', sa.Integer(), nullable=True),
        sa.Column('response_sha256', sa.String(), nullable=True),
        sa.Column('payload_bytes', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_idempotency_expires', 'idempotency_keys', ['expires_at'])

    op.create_table(
        'outbox',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('payload_json', sa.JSON(), nullable=False),
        sa.Column('dedup_key', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('NEW', 'SENT', 'FAILED', name='outboxstatus'), server_default='NEW', nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_outbox_status', 'outbox', ['status'])
    op.create_index('idx_outbox_next_retry', 'outbox', ['next_retry_at'])


def downgrade():
    op.drop_index('idx_outbox_next_retry', table_name='outbox')
    op.drop_index('idx_outbox_status', table_name='outbox')
    op.drop_table('outbox')
    sa.Enum('NEW', 'SENT', 'FAILED', name='outboxstatus').drop(op.get_bind(), checkfirst=False)
    op.drop_index('idx_idempotency_expires', table_name='idempotency_keys')
    op.drop_table('idempotency_keys')
