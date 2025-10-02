-- Hierarchical comments for nodes
CREATE TABLE IF NOT EXISTS node_comments (
    id bigserial PRIMARY KEY,
    node_id bigint NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    author_id uuid NOT NULL,
    parent_comment_id bigint NULL REFERENCES node_comments(id) ON DELETE CASCADE,
    depth smallint NOT NULL DEFAULT 0,
    content text NOT NULL,
    status text NOT NULL DEFAULT 'published',
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE node_comments
    ADD CONSTRAINT node_comments_status_chk
    CHECK (status IN ('pending', 'published', 'hidden', 'deleted', 'blocked'));
ALTER TABLE node_comments
    ADD CONSTRAINT node_comments_depth_chk
    CHECK (depth >= 0 AND depth <= 5);

CREATE INDEX IF NOT EXISTS ix_node_comments_node_created
    ON node_comments (node_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_node_comments_parent
    ON node_comments (parent_comment_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_node_comments_author
    ON node_comments (author_id, created_at DESC);

-- User-level bans for comments
CREATE TABLE IF NOT EXISTS node_comment_bans (
    node_id bigint NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_user_id uuid NOT NULL,
    set_by uuid NOT NULL,
    reason text NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (node_id, target_user_id)
);

CREATE INDEX IF NOT EXISTS ix_node_comment_bans_set_by
    ON node_comment_bans (set_by, created_at DESC);
