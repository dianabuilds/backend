-- Strategy weights for navigation relations blending
CREATE TABLE IF NOT EXISTS navigation_strategy_config (
  strategy text PRIMARY KEY,
  weight double precision NOT NULL DEFAULT 0.25,
  enabled boolean NOT NULL DEFAULT true,
  updated_at timestamptz NOT NULL DEFAULT now(),
  meta jsonb NOT NULL DEFAULT '{}'::jsonb
);

INSERT INTO navigation_strategy_config(strategy, weight, enabled)
VALUES
  ('random', 0.25, true),
  ('tags', 0.35, true),
  ('embedding', 0.30, true),
  ('explore', 0.10, true)
ON CONFLICT (strategy) DO NOTHING;