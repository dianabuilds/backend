-- Extend notifications table for compatibility with legacy model
ALTER TABLE IF EXISTS notifications
  ADD COLUMN IF NOT EXISTS profile_id uuid NULL,
  ADD COLUMN IF NOT EXISTS status text NULL,
  ADD COLUMN IF NOT EXISTS version int NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS visibility text NULL,
  ADD COLUMN IF NOT EXISTS created_by_user_id uuid NULL,
  ADD COLUMN IF NOT EXISTS updated_by_user_id uuid NULL;

