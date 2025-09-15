-- Moderation: notes per case
CREATE TABLE IF NOT EXISTS product_moderation_notes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL REFERENCES product_moderation_cases(id) ON DELETE CASCADE,
  author_id uuid NULL,
  data jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_product_moderation_notes_case ON product_moderation_notes(case_id);

