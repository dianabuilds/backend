-- Product worlds (templates)
CREATE TABLE IF NOT EXISTS product_worlds (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL,
  title text NOT NULL,
  locale text NULL,
  description text NULL,
  meta jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  created_by_user_id uuid NULL,
  updated_by_user_id uuid NULL
);
CREATE INDEX IF NOT EXISTS ix_product_worlds_workspace ON product_worlds(workspace_id, created_at DESC);

