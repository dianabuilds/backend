-- Referral events
CREATE TABLE IF NOT EXISTS referral_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code_id uuid NULL REFERENCES referral_codes(id) ON DELETE SET NULL,
  code text NULL,
  referrer_user_id uuid NULL,
  referee_user_id uuid NOT NULL,
  event_type text NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  meta jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS ix_referral_events_referee ON referral_events(referee_user_id);
CREATE INDEX IF NOT EXISTS ix_referral_events_referrer ON referral_events(referrer_user_id);

