-- In-app notifications table (legacy-compatible simplified)
CREATE TYPE IF NOT EXISTS notificationplacement AS ENUM ('inbox','banner');
CREATE TYPE IF NOT EXISTS notificationtype AS ENUM ('system','user');

CREATE TABLE IF NOT EXISTS notifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  title text NOT NULL,
  message text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  read_at timestamptz NULL,
  type notificationtype NOT NULL DEFAULT 'system',
  placement notificationplacement NOT NULL DEFAULT 'inbox',
  is_preview boolean NOT NULL DEFAULT false
);
CREATE INDEX IF NOT EXISTS ix_notifications_user ON notifications(user_id, created_at DESC);

