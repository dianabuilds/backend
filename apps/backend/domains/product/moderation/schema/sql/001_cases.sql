-- Moderation: cases
CREATE TABLE IF NOT EXISTS product_moderation_cases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  status text NOT NULL DEFAULT 'open',
  data jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  created_by_user_id uuid NULL
);
CREATE INDEX IF NOT EXISTS ix_product_moderation_cases_status ON product_moderation_cases(status);
CREATE INDEX IF NOT EXISTS ix_product_moderation_cases_created ON product_moderation_cases(created_at DESC);

