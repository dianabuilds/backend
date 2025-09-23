CREATE TABLE IF NOT EXISTS crypto_config (
  slug text PRIMARY KEY,
  config jsonb NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

