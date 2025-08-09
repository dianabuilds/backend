from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7f2b8e536ab1'
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in cols


def upgrade():
    bind = op.get_bind()

    # Enums
    user_role = sa.Enum('user', 'moderator', 'admin', name='user_role')
    user_role.create(bind, checkfirst=True)

    restriction_type = sa.Enum('ban', 'post_restrict', name='restriction_type')
    restriction_type.create(bind, checkfirst=True)

    # users.role
    if _table_exists('users') and not _column_exists('users', 'role'):
        op.add_column('users', sa.Column('role', user_role, nullable=False, server_default='user'))
        # снимаем server_default для чистоты схемы
        op.alter_column('users', 'role', server_default=None)

    # nodes.is_visible
    if _table_exists('nodes') and not _column_exists('nodes', 'is_visible'):
        op.add_column('nodes', sa.Column('is_visible', sa.Boolean(), nullable=False, server_default=sa.true()))
        op.alter_column('nodes', 'is_visible', server_default=None)

    # user_restrictions
    if not _table_exists('user_restrictions'):
        op.create_table(
            'user_restrictions',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('type', restriction_type, nullable=False),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('issued_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['issued_by'], ['users.id']),
        )

    # node_moderation
    if not _table_exists('node_moderation'):
        op.create_table(
            'node_moderation',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('node_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('hidden_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['node_id'], ['nodes.id']),
            sa.ForeignKeyConstraint(['hidden_by'], ['users.id']),
        )


def downgrade():
    # Удаляем таблицы, если существуют
    if _table_exists('node_moderation'):
        op.drop_table('node_moderation')
    if _table_exists('user_restrictions'):
        op.drop_table('user_restrictions')

    # Удаляем колонки, если существуют
    if _table_exists('nodes') and _column_exists('nodes', 'is_visible'):
        op.drop_column('nodes', 'is_visible')
    if _table_exists('users') and _column_exists('users', 'role'):
        op.drop_column('users', 'role')

    # Удаляем типы перечислений
    op.execute('DROP TYPE IF EXISTS restriction_type')
    op.execute('DROP TYPE IF EXISTS user_role')
