"""Add performance indexes for nodes and notifications.

Revision ID: 0110_nodes_notifications_indexes
Revises: 0109_home_config_drop_slug_unique
Create Date: 2025-10-12
"""

from __future__ import annotations

from alembic import op

revision = "0110_nodes_notifications_indexes"
down_revision = "0109_home_config_drop_slug_unique"
branch_labels = None
depends_on = None


_CREATE_INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_nodes_author_id_id ON nodes (author_id, id DESC)",
    "CREATE INDEX IF NOT EXISTS ix_product_node_tags_node_slug ON product_node_tags (node_id, slug)",
    "CREATE INDEX IF NOT EXISTS ix_notification_receipts_user_placement_created ON notification_receipts (user_id, placement, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_notification_receipts_event_id ON notification_receipts (event_id)",
    "CREATE INDEX IF NOT EXISTS ix_moderation_cases_status_lower ON moderation_cases ((lower(status)))",
    "CREATE INDEX IF NOT EXISTS ix_moderation_cases_type_lower ON moderation_cases ((lower(data->>'type')))",
    "CREATE INDEX IF NOT EXISTS ix_moderation_cases_queue_lower ON moderation_cases ((lower(data->>'queue')))",
    "CREATE INDEX IF NOT EXISTS ix_moderation_cases_assignee ON moderation_cases ((data->>'assignee_id'))",
)

_DROP_INDEXES = (
    "DROP INDEX IF EXISTS ix_nodes_author_id_id",
    "DROP INDEX IF EXISTS ix_product_node_tags_node_slug",
    "DROP INDEX IF EXISTS ix_notification_receipts_user_placement_created",
    "DROP INDEX IF EXISTS ix_notification_receipts_event_id",
    "DROP INDEX IF EXISTS ix_moderation_cases_status_lower",
    "DROP INDEX IF EXISTS ix_moderation_cases_type_lower",
    "DROP INDEX IF EXISTS ix_moderation_cases_queue_lower",
    "DROP INDEX IF EXISTS ix_moderation_cases_assignee",
)


def upgrade() -> None:
    for statement in _CREATE_INDEXES:
        op.execute(statement)


def downgrade() -> None:
    for statement in _DROP_INDEXES:
        op.execute(statement)
