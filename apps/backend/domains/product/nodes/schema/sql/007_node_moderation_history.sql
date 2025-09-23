-- Store moderation decisions history for nodes
CREATE TABLE IF NOT EXISTS node_moderation_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id bigint NOT NULL,
  action text NOT NULL,
  status text NOT NULL,
  reason text NULL,
  actor_id text NULL,
  decided_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS ix_node_moderation_history_node ON node_moderation_history(node_id, decided_at DESC);