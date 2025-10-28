CREATE TABLE IF NOT EXISTS crypto_config (
  slug text PRIMARY KEY,
  rpc_endpoints jsonb NOT NULL DEFAULT '{}'::jsonb,
  fallback_networks jsonb NOT NULL DEFAULT '{}'::jsonb,
  retries int NOT NULL DEFAULT 3,
  gas_price_cap numeric(24, 8) NULL,
  extra jsonb NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
