from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240601_add_feedback'
down_revision = '20240520_add_embeddings_echo'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'nodes',
        sa.Column('allow_feedback', sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.create_table(
        'feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('is_hidden', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('is_anonymous', sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index('idx_feedback_node', 'feedback', ['node_id'])
    op.create_index('idx_feedback_author', 'feedback', ['author_id'])


def downgrade():
    op.drop_index('idx_feedback_author', table_name='feedback')
    op.drop_index('idx_feedback_node', table_name='feedback')
    op.drop_table('feedback')
    op.drop_column('nodes', 'allow_feedback')
