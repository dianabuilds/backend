-- Referral codes
CREATE TABLE IF NOT EXISTS product_referral_codes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user_id uuid NOT NULL UNIQUE,
  code text NOT NULL UNIQUE,
  active boolean NOT NULL DEFAULT true,
  uses_count int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_product_referral_codes_code ON product_referral_codes(code);

