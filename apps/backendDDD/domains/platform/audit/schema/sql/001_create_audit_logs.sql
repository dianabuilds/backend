-- Postgres table for audit logs, compatible with legacy model
CREATE TABLE IF NOT EXISTS audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id uuid NULL,
  action text NOT NULL,
  resource_type text NULL,
  resource_id text NULL,
  workspace_id uuid NULL,
  before jsonb NULL,
  after jsonb NULL,
  override boolean NOT NULL DEFAULT false,
  reason text NULL,
  ip text NULL,
  user_agent text NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  extra jsonb NULL
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_resource ON audit_logs (resource_type, resource_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_workspace ON audit_logs (workspace_id);

