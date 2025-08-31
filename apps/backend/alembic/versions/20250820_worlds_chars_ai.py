from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250820_worlds_chars_ai"
down_revision = "20250820_pg_types_upgrade"
branch_labels = None
depends_on = None


def upgrade():
    # world_templates
    op.create_table(
        "world_templates",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("locale", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )

    # characters
    op.create_table(
        "characters",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "world_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("traits", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["world_id"], ["world_templates.id"], ondelete="CASCADE"
        ),
    )

    # ai_settings (одна строка конфигурации)
    op.create_table(
        "ai_settings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade():
    op.drop_table("characters")
    op.drop_table("world_templates")
    op.drop_table("ai_settings")
