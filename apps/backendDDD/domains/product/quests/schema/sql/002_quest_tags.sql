-- Quest tags table
CREATE TABLE IF NOT EXISTS product_quest_tags (
  quest_id uuid NOT NULL REFERENCES product_quests(id) ON DELETE CASCADE,
  slug text NOT NULL,
  PRIMARY KEY (quest_id, slug)
);
CREATE INDEX IF NOT EXISTS ix_product_quest_tags_slug ON product_quest_tags(slug);

