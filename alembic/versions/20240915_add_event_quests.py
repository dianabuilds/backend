from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20240915_add_event_quests'
down_revision = '20240901_enable_pgvector'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'event_quests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('target_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nodes.id'), nullable=False),
        sa.Column('hints_tags', sa.ARRAY(sa.String()), server_default='{}', nullable=False),
        sa.Column('hints_keywords', sa.ARRAY(sa.String()), server_default='{}', nullable=False),
        sa.Column('hints_trace', sa.ARRAY(postgresql.UUID(as_uuid=True)), server_default='{}', nullable=False),
        sa.Column('starts_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('max_rewards', sa.Integer(), server_default='0', nullable=False),
        sa.Column('reward_type', sa.Enum('achievement', 'premium', 'custom', name='eventquestrewardtype'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='false', nullable=False),
    )
    op.create_table(
        'event_quest_completions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('quest_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('event_quests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('quest_id', 'user_id', name='uq_event_quest_user'),
    )
    op.create_index('idx_event_quest_completions_quest', 'event_quest_completions', ['quest_id'])


def downgrade():
    op.drop_index('idx_event_quest_completions_quest', table_name='event_quest_completions')
    op.drop_table('event_quest_completions')
    op.drop_table('event_quests')
    sa.Enum('achievement', 'premium', 'custom', name='eventquestrewardtype').drop(op.get_bind(), checkfirst=False)
