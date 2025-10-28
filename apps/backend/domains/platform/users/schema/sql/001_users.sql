-- Legacy-compatible users table (minimal subset used by platform)
CREATE TYPE IF NOT EXISTS user_role AS ENUM ('user','support','editor','moderator','admin');

CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),

  -- Auth
  email text UNIQUE NULL,
  password_hash text NULL,
  wallet_address text UNIQUE NULL,

  -- Meta
  is_active boolean NOT NULL DEFAULT false,
  is_premium boolean NOT NULL DEFAULT false,
  premium_until timestamptz NULL,
  role user_role NOT NULL DEFAULT 'user',

  -- Profile
  username text UNIQUE NULL,
  bio text NULL,
  avatar_url text NULL,

  -- Activity
  last_login_at timestamptz NULL,

  -- GDPR
  deleted_at timestamptz NULL
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_wallet ON users(wallet_address);
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
