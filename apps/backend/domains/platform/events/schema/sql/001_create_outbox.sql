-- Transactional Outbox table (compatible with legacy model OutboxEvent)
CREATE TYPE IF NOT EXISTS outboxstatus AS ENUM ('NEW','SENT','FAILED');

CREATE TABLE IF NOT EXISTS outbox (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  topic text NOT NULL,
  payload_json jsonb NOT NULL,
  dedup_key text NULL,
  status outboxstatus NOT NULL DEFAULT 'NEW',
  attempts int NOT NULL DEFAULT 0,
  next_retry_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  workspace_id uuid NULL,
  is_preview boolean NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS ix_outbox_status_next ON outbox (status, next_retry_at);
CREATE INDEX IF NOT EXISTS ix_outbox_topic_created ON outbox (topic, created_at DESC);

