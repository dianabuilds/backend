"""
Add payment_contracts, payment_contract_events, and crypto_config tables.

Revision ID: 0011
Revises: 0010
Create Date: 2025-09-19
"""

from __future__ import annotations

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure pgcrypto for gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.execute(
        """
        -- Smart contracts registry
        CREATE TABLE IF NOT EXISTS payment_contracts (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          slug text NOT NULL UNIQUE,
          title text NULL,
          chain text NOT NULL,
          address text NOT NULL,
          type text NOT NULL,
          enabled boolean NOT NULL DEFAULT true,
          status text NOT NULL DEFAULT 'active',
          testnet boolean NOT NULL DEFAULT false,
          methods jsonb NULL,
          abi_present boolean NOT NULL DEFAULT false,
          webhook_url text NULL,
          abi jsonb NULL,
          created_at timestamptz NOT NULL DEFAULT now(),
          updated_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ux_payment_contracts_address ON payment_contracts(address);

        -- Contract events log
        CREATE TABLE IF NOT EXISTS payment_contract_events (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          contract_id uuid NOT NULL REFERENCES payment_contracts(id) ON DELETE CASCADE,
          event text NOT NULL,
          method text NULL,
          tx_hash text NULL,
          status text NULL,
          amount numeric NULL,
          token text NULL,
          meta jsonb NULL,
          created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS ix_contract_events_contract ON payment_contract_events(contract_id);
        CREATE INDEX IF NOT EXISTS ix_contract_events_created ON payment_contract_events(created_at);

        -- Crypto config (simple key-value JSON storage)
        CREATE TABLE IF NOT EXISTS crypto_config (
          slug text PRIMARY KEY,
          config jsonb NULL,
          updated_at timestamptz NOT NULL DEFAULT now()
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS payment_contract_events;")
    op.execute("DROP INDEX IF EXISTS ux_payment_contracts_address;")
    op.execute("DROP TABLE IF EXISTS payment_contracts;")
    op.execute("DROP TABLE IF EXISTS crypto_config;")
