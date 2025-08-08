from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20240801_add_achievements'
down_revision = '20240715_add_node_traces'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'achievements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(), nullable=False, unique=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('condition', postgresql.JSONB(), nullable=False),
        sa.Column('visible', sa.Boolean(), server_default='true', nullable=False),
    )
    op.create_table(
        'user_achievements',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('achievement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('achievements.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('unlocked_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_user_achievements_user', 'user_achievements', ['user_id'])
    op.create_index('idx_user_achievements_achievement', 'user_achievements', ['achievement_id'])


def downgrade():
    op.drop_index('idx_user_achievements_user', table_name='user_achievements')
    op.drop_index('idx_user_achievements_achievement', table_name='user_achievements')
    op.drop_table('user_achievements')
    op.drop_table('achievements')
