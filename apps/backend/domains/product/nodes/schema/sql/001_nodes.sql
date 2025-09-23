-- Product nodes main table
CREATE TABLE IF NOT EXISTS nodes (
  id bigserial PRIMARY KEY,
  author_id uuid NOT NULL,
  title text NULL,
  is_public boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_nodes_author ON nodes(author_id, id);

