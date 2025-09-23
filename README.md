## Feature Flags Management (Backend)

- FastAPI service exposing management endpoints for compact, safe Off/All/Premium feature flags.
- JSON persistence with audit history and revisions for rollback.
- Minimal admin page at `/management` with inline edits.

## Run

- Install deps: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --reload`
- Open: `http://127.0.0.1:8000/management`

Headers for RBAC:
- `X-User-Role: admin` is required for mutations. `moderator` can only read.
- `X-User-Id: 42` identifies the actor in audit.

Production safeguard:
- Changing production to enabled requires `?confirm=true` (API) and is prompted in the demo UI.

## Key Endpoints

- `GET /management/flags?env=production&state=on&group=AI&query=quest`
- `POST /management/flags` (create; default off/draft) body: `{ key, title, env, [preset] }`
- `PATCH /management/flags/{key}?env=...` (update fields)
- `POST /management/flags/{key}/rollback?env=...&to=0`
- `GET /management/flags/{key}/audit`
- `POST /management/flags/batch`
- `GET /management/flags/export?env=...` and `POST /management/flags/import`
- `POST /management/eval` to evaluate for a user

## Model (JSON)

Matches the spec with `state`, `audience`, `rollout`, `depends_on`, `schedule`, `env`, `updated_by`, `updated_at`, and `pinned`.

## Presets

- `toggle`: Off/All/Premium basic (created as off/off)
- `kill-switch`: One toggle, System group, audience off
- `gradual-rollout`: On + All, rollout 5% on staging

## Notes

- Storage files under `data/`: `flags.json`, `audit.json`, `revisions.json`.
- UI uses Tailwind CDN; drawer and history sidebar can be expanded similarly (out of demo scope).
