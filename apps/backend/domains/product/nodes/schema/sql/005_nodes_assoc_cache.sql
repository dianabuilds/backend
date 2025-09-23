-- Cache for related nodes (associations)
CREATE TABLE IF NOT EXISTS node_assoc_cache (
  source_id bigint NOT NULL,
  target_id bigint NOT NULL,
  algo text NOT NULL,
  score double precision NOT NULL DEFAULT 0,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (source_id, target_id, algo)
);
CREATE INDEX IF NOT EXISTS ix_node_assoc_cache_source_algo ON node_assoc_cache(source_id, algo, updated_at DESC);

