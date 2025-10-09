-- Node engagement counters on main table
ALTER TABLE nodes
    ADD COLUMN IF NOT EXISTS views_count bigint NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS reactions_like_count bigint NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS comments_disabled boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS comments_locked_by uuid NULL,
    ADD COLUMN IF NOT EXISTS comments_locked_at timestamptz NULL;

CREATE INDEX IF NOT EXISTS ix_nodes_views_count ON nodes (views_count DESC, id);
CREATE INDEX IF NOT EXISTS ix_nodes_reactions_like_count ON nodes (reactions_like_count DESC, id);
CREATE INDEX IF NOT EXISTS ix_nodes_comments_disabled ON nodes (comments_disabled, id);
