-- Grants of achievements to users
CREATE TABLE IF NOT EXISTS product_achievement_grants (
  user_id uuid NOT NULL,
  achievement_id uuid NOT NULL REFERENCES product_achievements(id) ON DELETE CASCADE,
  unlocked_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, achievement_id)
);
CREATE INDEX IF NOT EXISTS ix_product_achievement_grants_user ON product_achievement_grants(user_id);

