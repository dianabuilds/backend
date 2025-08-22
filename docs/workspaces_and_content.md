# Workspaces and Content

This document describes how content is organized inside workspaces and how it
moves through its lifecycle.

## Roles

Each workspace isolates data and permissions. A member has one of the following
roles:

- **Owner** – full control over the workspace, including settings and member
  management.
- **Editor** – can create, update and publish content.
- **Viewer** – read‑only access. Viewers cannot modify content or tags.

Global **admins** bypass workspace roles and can access any workspace.

## Status lifecycle

Content items progress through a simple workflow:

1. **draft** – freshly created item, visible only to editors.
2. **in_review** – ready for peer review and validation.
3. **published** – appears in user‑facing listings and APIs.
4. **archived** – kept for history but hidden from active lists.

Items typically move `draft → in_review → published`. Publishing again after an
edit sets the status back to `draft` until it passes review.

## Tag taxonomy

Tags classify content inside a workspace. Each tag has a stable `slug` and a
human‑readable `name`.

- Use **kebab‑case** slugs (e.g. `world-building`).
- Keep the taxonomy consistent by using prefixes such as `genre/`, `theme/` or
  `mechanic/`.
- Mark internal tags with `is_hidden` to exclude them from public lists.
- Merge or rename duplicates through the admin interface.

## Publication checklist

Before promoting a draft to `published`:

- Title and slug are unique within the workspace.
- Required tags are assigned and follow the taxonomy rules.
- `POST /admin/content/{type}/{id}/validate` returns no blocking issues.
- Cover media and other mandatory fields are set.
- Peer review is completed (`in_review`).
- Publish via `POST /admin/content/{type}/{id}/publish` and verify in the
  dashboard.

## API routes

Administrative endpoints exposed by the backend:

### Workspaces

- `GET /admin/workspaces` – list available workspaces.
- `POST /admin/workspaces/{workspace_id}` – create a workspace with a fixed ID.
- `GET /admin/workspaces/{workspace_id}` – fetch workspace metadata.
- `PATCH /admin/workspaces/{workspace_id}` – update workspace fields.
- `DELETE /admin/workspaces/{workspace_id}` – remove a workspace.

### Content

All content routes expect `workspace_id` as a query parameter.

- `GET /admin/content` – dashboard with counts of drafts, reviews and published
  items.
- `GET /admin/content/all` – list content items with optional filters
  (`content_type`, `status`, `tag`).
- `POST /admin/content/{type}` – create a new item of a given `type`.
- `GET /admin/content/{type}/{id}` – fetch a single content item.
- `PATCH /admin/content/{type}/{id}` – update an item.
- `POST /admin/content/{type}/{id}/publish` – mark the item as published.
- `POST /admin/content/{type}/{id}/validate` – run validators and return a
  report.

## Front‑end flows

The admin UI communicates with these routes:

- **Workspace selection** – `WorkspaceSelector` fetches `/admin/workspaces` and
  stores the chosen ID in session storage. The API client automatically appends
  `workspace_id` to subsequent calls.
- **Dashboard** – `ContentDashboard` calls `/admin/content` to show counts of
  drafts, reviews and published items.
- **Content list** – `ContentAll` uses `/admin/content/all` with filters for type,
  status and tag.
- **Tag management** – `TagMerge` and other components operate on tags using the
  standard admin tag endpoints.

