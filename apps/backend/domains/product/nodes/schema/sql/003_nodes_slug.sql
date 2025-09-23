-- Add slug support for nodes table (for fresh SQL bootstrap)
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS slug text;
UPDATE nodes
SET slug = SUBSTRING(md5(random()::text || clock_timestamp()::text) FOR 16)
WHERE slug IS NULL;
ALTER TABLE nodes ADD CONSTRAINT IF NOT EXISTS nodes_slug_format_chk CHECK (slug ~ '^[0-9a-f]{16}$');
CREATE UNIQUE INDEX IF NOT EXISTS ux_nodes_slug ON nodes(slug);
ALTER TABLE nodes ALTER COLUMN slug SET NOT NULL;

