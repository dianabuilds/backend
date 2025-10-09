# Feature Flags: SQL Rollout Guide

## Summary

Key platform slugs: `content.nodes`, `content.quests`, `notifications.broadcasts`, `billing.revenue`, `observability.core`, `moderation.guardrails`. The admin API now returns an `audience` hint (all/premium/testers/custom/disabled) and an `effective` boolean for every flag.

The FastAPI routes rely on application-level commands and queries: `domains.platform.flags.application.commands` handles mutations while `domains.platform.flags.application.queries` serves read checks; `application.presenter` remains responsible for DTO assembly only.

Feature flags use PostgreSQL as the single source of truth (`feature_flags`, `feature_flag_rules`, `feature_flag_audit`). The FastAPI service exposes structured flag data (status, rollout %, testers/roles/segments, audience) and `/v1/settings/features` returns a detailed map consumed by the web app.

## Schema

- `feature_flags` (`slug PK`, `description`, `status`, `rollout`, `meta`, `created_at`, `updated_at`, `created_by`, `updated_by`)
- `feature_flag_rules` (`flag_slug FK`, `type`, `value`, `rollout`, `priority`, `meta`, `created_at`, `created_by`)
- `feature_flag_audit` (append-only history of changes)
- Enums: `feature_flag_status` (`disabled`, `testers`, `premium`, `all`, `custom`) and `feature_flag_rule_type` (`user`, `segment`, `role`, `percentage`)

## Migration Checklist

1. **Deploy migration** – apply Alembic revision `0101_feature_flags_sql`.
2. **Import existing flags** – translate Redis dumps (if any) into SQL rows (`flag.slug`, `status`, `rollout`, `rules`).
3. **Verify configuration** – ensure `APP_DATABASE_URL` is set; Redis is no longer required for flags.
4. **Restart services/UI** – reload API Gateway and web app to pick up the new schema.
5. **Smoke test** –
   - `GET /v1/flags` returns structured payload (status, rollout %, audience hint, testers, timestamps).
   - `/v1/settings/features` returns objects with `enabled`, `effective`, `status`, `audience`, and metadata.
   - Management UI shows status/targeting columns and kill/enable actions.

## Evaluation Semantics

- Rules are processed in priority order (user > segment > role > percentage).
- Percentage rules use deterministic SHA256 buckets (`user_id` > 0..99).
- `FlagStatus` acts as fallback:
  - `disabled` > always off.
  - `testers` > only explicit rules.
  - `premium` > requires premium hints (`plan`, `roles`, `is_premium`).
  - `all` > everyone; optional global rollout %.
  - `custom` > defined entirely by rules.

## Admin API & UI

- `GET /v1/flags` – structured rows for the management UI.
- `POST /v1/flags` – accepts `status`, optional `rollout`, list fields (`testers`, `roles`, `segments`) or a raw `rules[]` array.
- `DELETE /v1/flags/{slug}` – remove flag.
- `GET /v1/flags/check/{slug}` – boolean evaluation helper.

The React management page (`apps/web/src/pages/management/Flags.tsx`) supports:
- Editing `status`, `rollout`, testers/roles/segments.
- Quick actions: kill switch and enable 100%.
- Viewing metadata (last update, rules, audience).

## Settings Integration

`/v1/settings/features` returns an object per feature with these fields:
- `slug`, `status`, `status_label`, `audience`, `enabled`, `effective`, `rollout`, `testers`, `roles`, `segments`, `rules`, `meta`, `created_at`, `updated_at`, `evaluated_at`.

The settings provider normalises this payload into `SettingsFeatureState`, and `useSettingsFeature` continues to return booleans for simple checks.

## Runbook

1. Apply migration and restart the backend.
2. Seed required flags (kill-switches, notification channels, etc.).
3. Double-check `/v1/flags` and `/v1/settings/features` responses.
4. Update environment documentation if deploying to new environments.
5. Communicate UI changes to admins (new audience selector, targeting inputs).
