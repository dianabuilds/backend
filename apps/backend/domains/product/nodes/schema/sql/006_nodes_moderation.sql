-- Moderation metadata for nodes
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS moderation_status text;
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS moderation_status_updated_at timestamptz;

UPDATE nodes
SET moderation_status = CASE
  WHEN moderation_status IS NOT NULL THEN moderation_status
  WHEN status IN ('published') THEN 'resolved'
  WHEN status IN ('deleted','archived') THEN 'hidden'
  ELSE 'pending'
END,
    moderation_status_updated_at = COALESCE(moderation_status_updated_at, updated_at)
WHERE moderation_status IS NULL;

ALTER TABLE nodes ADD CONSTRAINT IF NOT EXISTS nodes_moderation_status_chk CHECK (moderation_status IN ('pending','resolved','hidden','restricted','escalated'));
ALTER TABLE nodes ALTER COLUMN moderation_status SET NOT NULL;
ALTER TABLE nodes ALTER COLUMN moderation_status SET DEFAULT 'pending';
CREATE INDEX IF NOT EXISTS ix_nodes_moderation_status ON nodes (moderation_status, updated_at DESC);