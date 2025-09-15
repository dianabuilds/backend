-- Blacklisted slugs
CREATE TABLE IF NOT EXISTS product_tag_blacklist (
  slug text PRIMARY KEY,
  reason text NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

