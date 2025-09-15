-- Notification campaigns table (legacy-compatible)
CREATE TABLE IF NOT EXISTS notification_campaigns (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  message text NOT NULL,
  type text NOT NULL DEFAULT 'platform',
  filters jsonb NULL,
  status text NOT NULL DEFAULT 'draft',
  total int NOT NULL DEFAULT 0,
  sent int NOT NULL DEFAULT 0,
  failed int NOT NULL DEFAULT 0,
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz NULL,
  finished_at timestamptz NULL
);
CREATE INDEX IF NOT EXISTS ix_notification_campaigns_created ON notification_campaigns (created_at DESC);

