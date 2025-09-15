-- Referral events
CREATE TABLE IF NOT EXISTS product_referral_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code_id uuid NULL REFERENCES product_referral_codes(id) ON DELETE SET NULL,
  code text NULL,
  referrer_user_id uuid NULL,
  referee_user_id uuid NOT NULL,
  event_type text NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  meta jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS ix_product_referral_events_referee ON product_referral_events(referee_user_id);
CREATE INDEX IF NOT EXISTS ix_product_referral_events_referrer ON product_referral_events(referrer_user_id);

