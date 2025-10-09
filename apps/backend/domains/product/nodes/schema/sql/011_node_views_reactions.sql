-- Track node views aggregated by day
CREATE TABLE IF NOT EXISTS node_views_daily (
    node_id bigint NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    bucket_date date NOT NULL,
    views bigint NOT NULL DEFAULT 0,
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (node_id, bucket_date)
);

CREATE INDEX IF NOT EXISTS ix_node_views_daily_date ON node_views_daily (bucket_date DESC, node_id);

-- Store per-user reactions (likes)
CREATE TABLE IF NOT EXISTS node_reactions (
    id bigserial PRIMARY KEY,
    node_id bigint NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    user_id uuid NOT NULL,
    reaction_type text NOT NULL DEFAULT 'like',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_node_reactions_unique
    ON node_reactions (node_id, user_id, reaction_type);
CREATE INDEX IF NOT EXISTS ix_node_reactions_node ON node_reactions (node_id, reaction_type, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_node_reactions_user ON node_reactions (user_id, created_at DESC);

ALTER TABLE node_reactions
    ADD CONSTRAINT node_reactions_reaction_type_chk
    CHECK (char_length(reaction_type) >= 1 AND char_length(reaction_type) <= 32);
