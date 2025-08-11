from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20241101_add_audit_log'
down_revision = '20241020_add_source_channel_to_echo'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('before', postgresql.JSONB(), nullable=True),
        sa.Column('after', postgresql.JSONB(), nullable=True),
        sa.Column('ip', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('extra', postgresql.JSONB(), nullable=True),
    )
    op.create_index('idx_audit_logs_actor', 'audit_logs', ['actor_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_created', 'audit_logs', ['created_at'])


def downgrade():
    op.drop_index('idx_audit_logs_created', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_actor', table_name='audit_logs')
    op.drop_table('audit_logs')
