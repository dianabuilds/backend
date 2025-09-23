CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE nodes
    ADD COLUMN IF NOT EXISTS embedding vector(1536);

CREATE INDEX IF NOT EXISTS ix_nodes_embedding ON nodes USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
