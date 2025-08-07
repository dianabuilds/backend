from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7f2b8e536ab1'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    user_role = sa.Enum('user', 'moderator', 'admin', name='user_role')
    user_role.create(op.get_bind(), checkfirst=True)
    op.add_column('users', sa.Column('role', user_role, nullable=False, server_default='user'))

    op.add_column('nodes', sa.Column('is_visible', sa.Boolean(), nullable=False, server_default=sa.true()))

    restriction_type = sa.Enum('ban', 'post_restrict', name='restriction_type')
    restriction_type.create(op.get_bind(), checkfirst=True)

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
    op.drop_table('node_moderation')
    op.drop_table('user_restrictions')
    op.drop_column('nodes', 'is_visible')
    op.drop_column('users', 'role')
    op.execute('DROP TYPE IF EXISTS restriction_type')
    op.execute('DROP TYPE IF EXISTS user_role')
