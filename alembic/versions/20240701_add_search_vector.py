from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20240701_add_search_vector'
down_revision = '20240615_add_tags'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('quests', sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True))
    op.execute("""
    CREATE INDEX idx_quests_search_vector
    ON quests
    USING GIN(search_vector);
    """)
    op.execute("""
    CREATE FUNCTION quests_search_vector_update() RETURNS trigger AS $$
    BEGIN
      NEW.search_vector :=
        to_tsvector('simple', coalesce(NEW.title, '') || ' ' || coalesce(NEW.subtitle, '') || ' ' || coalesce(NEW.description, ''));
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)
    op.execute("""
    CREATE TRIGGER trg_quests_search_vector
    BEFORE INSERT OR UPDATE
    ON quests
    FOR EACH ROW
    EXECUTE FUNCTION quests_search_vector_update();
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_quests_search_vector ON quests")
    op.execute("DROP FUNCTION IF EXISTS quests_search_vector_update")
    op.drop_index('idx_quests_search_vector', table_name='quests')
    op.drop_column('quests', 'search_vector')
