-- Aliases for tags
CREATE TABLE IF NOT EXISTS product_tag_alias (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tag_id uuid NOT NULL REFERENCES product_tag(id) ON DELETE CASCADE,
  alias text UNIQUE NOT NULL,
  type text NOT NULL DEFAULT 'alias',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_product_tag_alias_tag ON product_tag_alias(tag_id);

