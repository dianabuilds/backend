-- Grants of achievements to users
CREATE TABLE IF NOT EXISTS achievement_grants (
  user_id uuid NOT NULL,
  achievement_id uuid NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
  unlocked_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, achievement_id)
);
CREATE INDEX IF NOT EXISTS ix_achievement_grants_user ON achievement_grants(user_id);

