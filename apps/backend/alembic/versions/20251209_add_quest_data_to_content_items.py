"""add quest_data to content items"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20251209_add_quest_data_to_content_items"
down_revision = "20251208_rename_content_patches_to_node_patches"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "content_items",
        sa.Column("quest_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute(
        """
        UPDATE content_items ci
        SET quest_data = jsonb_strip_nulls(jsonb_build_object(
            'subtitle', q.subtitle,
            'description', q.description,
            'cover_image', q.cover_image,
            'tags', q.tags,
            'price', q.price,
            'is_premium_only', q.is_premium_only,
            'entry_node_id', q.entry_node_id,
            'nodes', q.nodes,
            'custom_transitions', q.custom_transitions,
            'structure', q.structure,
            'length', q.length,
            'tone', q.tone,
            'genre', q.genre,
            'locale', q.locale,
            'cost_generation', q.cost_generation,
            'allow_comments', q.allow_comments,
            'is_deleted', q.is_deleted
        ))
        FROM quests q
        WHERE q.id = ci.id
        """
    )


def downgrade() -> None:
    op.drop_column("content_items", "quest_data")
