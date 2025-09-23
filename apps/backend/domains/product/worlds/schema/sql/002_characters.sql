-- Characters within a world
CREATE TABLE IF NOT EXISTS world_characters (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  world_id uuid NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
  name text NOT NULL,
  role text NULL,
  description text NULL,
  traits jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  created_by_user_id uuid NULL,
  updated_by_user_id uuid NULL
);
CREATE INDEX IF NOT EXISTS ix_world_characters_world ON world_characters(world_id);

