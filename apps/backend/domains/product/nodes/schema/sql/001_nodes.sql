-- Product nodes main table
CREATE TABLE IF NOT EXISTS product_nodes (
  id bigserial PRIMARY KEY,
  author_id uuid NOT NULL,
  title text NULL,
  is_public boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_product_nodes_author ON product_nodes(author_id, id);

