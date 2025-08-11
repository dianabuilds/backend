from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241101_add_payments'
down_revision = '20241020_add_source_channel_to_echo'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source', sa.Enum('manual', 'webhook', name='payment_source'), nullable=False),
        sa.Column('days', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'confirmed', 'failed', 'cancelled', name='payment_status'), server_default='pending', nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_payments_user', 'payments', ['user_id'])


def downgrade():
    op.drop_index('idx_payments_user', table_name='payments')
    op.drop_table('payments')
    sa.Enum('pending', 'confirmed', 'failed', 'cancelled', name='payment_status').drop(op.get_bind(), checkfirst=False)
    sa.Enum('manual', 'webhook', name='payment_source').drop(op.get_bind(), checkfirst=False)
