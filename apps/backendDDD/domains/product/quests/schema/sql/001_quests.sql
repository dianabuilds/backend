-- Product quests main table
CREATE TABLE IF NOT EXISTS product_quests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  author_id uuid NOT NULL,
  slug text UNIQUE NOT NULL,
  title text NOT NULL,
  description text NULL,
  is_public boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_product_quests_author ON product_quests(author_id, created_at DESC);

