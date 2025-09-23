-- Blacklisted slugs
CREATE TABLE IF NOT EXISTS tag_blacklist (
  slug text PRIMARY KEY,
  reason text NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

