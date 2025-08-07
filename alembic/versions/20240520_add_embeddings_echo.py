from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover
    Vector = sa.LargeBinary

# revision identifiers, used by Alembic.
revision = '20240520_add_embeddings_echo'
down_revision = '7f2b8e536ab1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('nodes', sa.Column('embedding_vector', Vector(dim=384)))
    op.execute(
        'CREATE INDEX IF NOT EXISTS idx_node_embedding_vector ON nodes USING ivfflat (embedding_vector vector_cosine_ops)'
    )
    op.create_table(
        'echo_trace',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('from_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nodes.id')),
        sa.Column('to_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('nodes.id')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('idx_echo_from_node', 'echo_trace', ['from_node_id'])


def downgrade():
    op.drop_index('idx_echo_from_node', table_name='echo_trace')
    op.drop_table('echo_trace')
    op.drop_index('idx_node_embedding_vector', table_name='nodes')
    op.drop_column('nodes', 'embedding_vector')
