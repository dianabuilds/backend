from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20240715_add_node_traces'
down_revision = '20240701_add_search_vector'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'node_traces',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('kind', sa.Enum('auto', 'manual', 'quest_hint', name='nodetracekind'), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('tags', sa.ARRAY(sa.String()), server_default='{}', nullable=False),
        sa.Column('visibility', sa.Enum('public', 'private', 'system', name='nodetracevisibility'), server_default='public', nullable=False),
    )
    op.create_index('idx_node_traces_node', 'node_traces', ['node_id'])


def downgrade():
    op.drop_index('idx_node_traces_node', table_name='node_traces')
    op.drop_table('node_traces')
    sa.Enum('auto', 'manual', 'quest_hint', name='nodetracekind').drop(op.get_bind(), checkfirst=False)
    sa.Enum('public', 'private', 'system', name='nodetracevisibility').drop(op.get_bind(), checkfirst=False)
