-- Node tags (many-to-many via slugs)
CREATE TABLE IF NOT EXISTS product_node_tags (
  node_id bigint NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  slug text NOT NULL,
  PRIMARY KEY (node_id, slug)
);
CREATE INDEX IF NOT EXISTS ix_product_node_tags_slug ON product_node_tags(slug);

