-- Create or upsert an admin-like user and issue a long-lived token.
--
-- Usage (PowerShell):
--   psql "$env:DATABASE_URL" -v ON_ERROR_STOP=1 \
--     -v email='admin@example.com' -v name='Admin' -v days=365 \
--     -f apps/backend/scripts/db/seed_admin.sql
--
-- Usage (bash):
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 \
--     -v email='admin@example.com' -v name='Admin' -v days=365 \
--     -f apps/backend/scripts/db/seed_admin.sql

DO $$ BEGIN
  CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- for gen_random_bytes(), crypt(), gen_salt()
END $$;

-- Defaults if not provided by -v flags
\set email :email
\if :{?username}
\else
  \set username 'admin'
\endif
\if :{?name}
\else
  \set name 'Admin'
\endif
\if :{?days}
\else
  \set days 365
\endif

WITH upsert_user AS (
  INSERT INTO users (email, username, display_name, is_active)
  VALUES (:'email', :'username', :'name', TRUE)
  ON CONFLICT (email) DO UPDATE
    SET display_name = EXCLUDED.display_name,
        is_active    = TRUE
  RETURNING id
), new_token AS (
  INSERT INTO user_tokens (user_id, token, expires_at)
  SELECT id,
         encode(gen_random_bytes(32), 'hex') AS token,
         now() + (:'days' || ' days')::interval
  FROM upsert_user
  RETURNING token
)
SELECT 'TOKEN=' || token AS admin_token
FROM new_token;

-- Optional: set a password hash when -v password='...'
-- Adds column if it doesn't exist yet.
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS password_hash text;
\if :{?password}
  UPDATE users
  SET password_hash = crypt(:'password', gen_salt('bf'))
  WHERE email = :'email';
  \echo Password hash set for :'email'
\endif

-- Grant roles if role system is present
DO $$
BEGIN
  IF to_regclass('user_roles') IS NOT NULL THEN
    INSERT INTO user_roles (user_id, role)
    SELECT id, 'user'::user_role FROM users WHERE email = :'email'
    ON CONFLICT DO NOTHING;

    INSERT INTO user_roles (user_id, role)
    SELECT id, 'admin'::user_role FROM users WHERE email = :'email'
    ON CONFLICT DO NOTHING;
  END IF;
END$$;

-- Also create a persistent session and refresh tokens for admin (dev convenience)
-- Note: tokens are returned in clear; in production issue via API only.
\if :{?create_session}
  WITH u AS (
    SELECT id FROM users WHERE email = :'email'
  ), tokens AS (
    SELECT
      encode(gen_random_bytes(32), 'hex') AS session_token,
      encode(gen_random_bytes(32), 'hex') AS refresh_token
  ), ins AS (
    INSERT INTO user_sessions (user_id, session_token_hash, refresh_token_hash, expires_at, refresh_expires_at)
    SELECT u.id,
           encode(digest(t.session_token, 'sha256'), 'hex'),
           encode(digest(t.refresh_token, 'sha256'), 'hex'),
           now() + (:'days' || ' days')::interval,
           now() + ((:'days'::int * 4) || ' days')::interval
    FROM u, tokens t
    RETURNING 1
  )
  SELECT 'SESSION=' || session_token, 'REFRESH=' || refresh_token FROM tokens;
\endif
