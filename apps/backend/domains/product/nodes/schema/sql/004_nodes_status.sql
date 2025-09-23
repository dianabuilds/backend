-- Add status / scheduling columns (for fresh bootstrap)
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS status text;
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS publish_at timestamptz NULL;
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS unpublish_at timestamptz NULL;
UPDATE nodes SET status = CASE WHEN is_public THEN 'published' ELSE 'draft' END WHERE status IS NULL;
ALTER TABLE nodes ADD CONSTRAINT IF NOT EXISTS nodes_status_chk CHECK (status IN ('draft','scheduled','published','scheduled_unpublish','archived','deleted'));
ALTER TABLE nodes ALTER COLUMN status SET NOT NULL;
CREATE INDEX IF NOT EXISTS ix_nodes_status_publish_at ON nodes(status, publish_at);
CREATE INDEX IF NOT EXISTS ix_nodes_status_unpublish_at ON nodes(status, unpublish_at);

