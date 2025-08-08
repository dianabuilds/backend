from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240615_add_tags'
down_revision = '20240601_add_feedback'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('is_hidden', sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index('idx_tag_slug', 'tags', ['slug'], unique=True)
    op.create_table(
        'node_tags',
        sa.Column('node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nodes.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.drop_column('nodes', 'tags')


def downgrade():
    op.add_column('nodes', sa.Column('tags', sa.ARRAY(sa.String())))
    op.drop_table('node_tags')
    op.drop_index('idx_tag_slug', table_name='tags')
    op.drop_table('tags')
