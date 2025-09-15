-- Aggregated usage counters by author/content_type/slug
CREATE TABLE IF NOT EXISTS product_tag_usage_counters (
  author_id uuid NOT NULL,
  content_type text NOT NULL,
  slug text NOT NULL,
  count int NOT NULL DEFAULT 0,
  PRIMARY KEY (author_id, content_type, slug)
);
CREATE INDEX IF NOT EXISTS ix_product_tag_usage_slug ON product_tag_usage_counters(slug);
CREATE INDEX IF NOT EXISTS ix_product_tag_usage_ctype ON product_tag_usage_counters(content_type);

