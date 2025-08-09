from alembic import op
import sqlalchemy as sa

revision = '20240901_enable_pgvector'
down_revision = '20240801_add_achievements'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("DROP INDEX IF EXISTS idx_node_embedding_vector")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_node_embedding_vector "
        "ON nodes USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return
    op.execute("DROP INDEX IF EXISTS idx_node_embedding_vector")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_node_embedding_vector "
        "ON nodes USING ivfflat (embedding_vector vector_cosine_ops)"
    )
