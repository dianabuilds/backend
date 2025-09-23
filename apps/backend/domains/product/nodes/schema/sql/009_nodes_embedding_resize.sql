CREATE EXTENSION IF NOT EXISTS vector;

DROP INDEX IF EXISTS ix_nodes_embedding;

ALTER TABLE nodes
    DROP COLUMN IF EXISTS embedding;

ALTER TABLE nodes
    ADD COLUMN embedding vector(1536);

CREATE INDEX IF NOT EXISTS ix_nodes_embedding ON nodes USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
