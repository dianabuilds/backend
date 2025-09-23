"""
Align audit_logs and outbox schema with current code expectations.

Revision ID: 0012
Revises: 0011
Create Date: 2025-09-20
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- audit_logs ---
    # Add/rename columns to match domains.platform.audit expectations
    op.execute(
        """
        DO $$
        BEGIN
            -- Add resource_type if missing
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audit_logs' AND column_name = 'resource_type'
            ) THEN
                ALTER TABLE audit_logs ADD COLUMN resource_type text NULL;
            END IF;

            -- If legacy entity_type exists, copy and drop
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audit_logs' AND column_name = 'entity_type'
            ) THEN
                UPDATE audit_logs SET resource_type = COALESCE(resource_type, entity_type);
                ALTER TABLE audit_logs DROP COLUMN entity_type;
            END IF;

            -- Ensure resource_id as TEXT; migrate from legacy entity_id (uuid)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audit_logs' AND column_name = 'resource_id'
            ) THEN
                ALTER TABLE audit_logs ADD COLUMN resource_id text NULL;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audit_logs' AND column_name = 'entity_id'
            ) THEN
                UPDATE audit_logs SET resource_id = COALESCE(resource_id, entity_id::text);
                ALTER TABLE audit_logs DROP COLUMN entity_id;
            END IF;

            -- Rename meta -> extra if extra missing and meta present
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audit_logs' AND column_name = 'extra'
            ) AND EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audit_logs' AND column_name = 'meta'
            ) THEN
                ALTER TABLE audit_logs RENAME COLUMN meta TO extra;
            END IF;

            -- Add additional optional columns used by repository
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audit_logs' AND column_name = 'workspace_id'
            ) THEN
                ALTER TABLE audit_logs ADD COLUMN workspace_id uuid NULL;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audit_logs' AND column_name = 'before'
            ) THEN
                ALTER TABLE audit_logs ADD COLUMN before jsonb NULL;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audit_logs' AND column_name = 'after'
            ) THEN
                ALTER TABLE audit_logs ADD COLUMN after jsonb NULL;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audit_logs' AND column_name = 'override'
            ) THEN
                ALTER TABLE audit_logs ADD COLUMN override boolean NOT NULL DEFAULT false;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audit_logs' AND column_name = 'reason'
            ) THEN
                ALTER TABLE audit_logs ADD COLUMN reason text NULL;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audit_logs' AND column_name = 'ip'
            ) THEN
                ALTER TABLE audit_logs ADD COLUMN ip text NULL;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'audit_logs' AND column_name = 'user_agent'
            ) THEN
                ALTER TABLE audit_logs ADD COLUMN user_agent text NULL;
            END IF;
        END$$;
        """
    )

    # --- outbox ---
    # Bring outbox in line with Events SQLOutbox expectations
    op.execute(
        """
        DO $$
        BEGIN
            -- payload_json column (copy from legacy payload)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'outbox' AND column_name = 'payload_json'
            ) THEN
                ALTER TABLE outbox ADD COLUMN payload_json jsonb NULL;
            END IF;
            -- Backfill from payload if present
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'outbox' AND column_name = 'payload'
            ) THEN
                UPDATE outbox SET payload_json = COALESCE(payload_json, payload);
            END IF;

            -- dedup_key column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'outbox' AND column_name = 'dedup_key'
            ) THEN
                ALTER TABLE outbox ADD COLUMN dedup_key text NULL;
            END IF;

            -- attempts column (do not drop legacy attempt)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'outbox' AND column_name = 'attempts'
            ) THEN
                ALTER TABLE outbox ADD COLUMN attempts integer NOT NULL DEFAULT 0;
            END IF;

            -- next_retry_at column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'outbox' AND column_name = 'next_retry_at'
            ) THEN
                ALTER TABLE outbox ADD COLUMN next_retry_at timestamptz NOT NULL DEFAULT now();
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    # Conservative downgrade: do not try to restore dropped legacy columns except straightforward cases
    op.execute(
        """
        DO $$
        BEGIN
            -- outbox: drop added columns if exist
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'outbox' AND column_name = 'next_retry_at'
            ) THEN
                ALTER TABLE outbox DROP COLUMN next_retry_at;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'outbox' AND column_name = 'attempts'
            ) THEN
                ALTER TABLE outbox DROP COLUMN attempts;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'outbox' AND column_name = 'dedup_key'
            ) THEN
                ALTER TABLE outbox DROP COLUMN dedup_key;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'outbox' AND column_name = 'payload_json'
            ) THEN
                ALTER TABLE outbox DROP COLUMN payload_json;
            END IF;

            -- audit_logs: drop added columns; recreate legacy ones where safe
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'user_agent'
            ) THEN
                ALTER TABLE audit_logs DROP COLUMN user_agent;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'ip'
            ) THEN
                ALTER TABLE audit_logs DROP COLUMN ip;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'reason'
            ) THEN
                ALTER TABLE audit_logs DROP COLUMN reason;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'override'
            ) THEN
                ALTER TABLE audit_logs DROP COLUMN override;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'after'
            ) THEN
                ALTER TABLE audit_logs DROP COLUMN "after";
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'before'
            ) THEN
                ALTER TABLE audit_logs DROP COLUMN before;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'workspace_id'
            ) THEN
                ALTER TABLE audit_logs DROP COLUMN workspace_id;
            END IF;
            -- Rename extra back to meta if meta missing
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'meta'
            ) AND EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'extra'
            ) THEN
                ALTER TABLE audit_logs RENAME COLUMN extra TO meta;
            END IF;
            -- Try to restore entity_type/entity_id if missing (best-effort)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'entity_type'
            ) THEN
                ALTER TABLE audit_logs ADD COLUMN entity_type text NULL;
                UPDATE audit_logs SET entity_type = resource_type WHERE entity_type IS NULL;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'entity_id'
            ) THEN
                ALTER TABLE audit_logs ADD COLUMN entity_id uuid NULL;
                -- Cast resource_id back to uuid where possible
                BEGIN
                    EXECUTE 'UPDATE audit_logs SET entity_id = resource_id::uuid WHERE resource_id ~ ''^[0-9a-fA-F-]{36}$'' ';
                EXCEPTION WHEN others THEN
                    -- ignore failures
                END;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'resource_type'
            ) THEN
                ALTER TABLE audit_logs DROP COLUMN resource_type;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'resource_id'
            ) THEN
                ALTER TABLE audit_logs DROP COLUMN resource_id;
            END IF;
        END$$;
        """
    )
