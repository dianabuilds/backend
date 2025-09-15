-- Subscription plans
CREATE TABLE IF NOT EXISTS subscription_plans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  title text NOT NULL,
  description text NULL,
  price_cents int NULL,
  currency text NULL DEFAULT 'USD',
  is_active boolean NOT NULL DEFAULT true,
  "order" int NOT NULL DEFAULT 100,
  monthly_limits jsonb NULL,
  features jsonb NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- User subscriptions
CREATE TABLE IF NOT EXISTS user_subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  plan_id uuid NOT NULL REFERENCES subscription_plans(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'active',
  auto_renew boolean NOT NULL DEFAULT false,
  started_at timestamptz NOT NULL DEFAULT now(),
  ends_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_user_subscriptions_user ON user_subscriptions(user_id);

-- Payment transactions (ledger)
CREATE TABLE IF NOT EXISTS payment_transactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  gateway_slug text NULL,
  product_type text NOT NULL,
  product_id uuid NULL,
  currency text NULL DEFAULT 'USD',
  gross_cents int NOT NULL,
  fee_cents int NOT NULL DEFAULT 0,
  net_cents int NOT NULL,
  status text NOT NULL DEFAULT 'captured',
  created_at timestamptz NOT NULL DEFAULT now(),
  meta jsonb NULL
);
CREATE INDEX IF NOT EXISTS ix_payment_tx_user ON payment_transactions(user_id);
CREATE INDEX IF NOT EXISTS ix_payment_tx_gateway ON payment_transactions(gateway_slug);

-- Payment gateways
CREATE TABLE IF NOT EXISTS payment_gateways (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  type text NOT NULL,
  enabled boolean NOT NULL DEFAULT true,
  priority int NOT NULL DEFAULT 100,
  config jsonb NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

