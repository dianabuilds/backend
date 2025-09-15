-- Legacy-compatible table for storing AI generation stage logs
CREATE TABLE IF NOT EXISTS generation_job_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id uuid NOT NULL,
  stage text NOT NULL,
  provider text NULL,
  model text NULL,
  prompt text NULL,
  raw_response text NULL,
  raw_url text NULL,
  raw_preview text NULL,
  usage jsonb NULL,
  cost double precision NULL,
  status text NOT NULL DEFAULT 'ok',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_generation_job_logs_job_id ON generation_job_logs (job_id);

