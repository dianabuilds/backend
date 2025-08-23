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

Example:

```bash
GET /admin/workspaces
```

```json
[
  {
    "id": "8b112b04-1769-44ef-abc6-3c7ce7c8de4e",
    "name": "Main workspace",
    "slug": "main",
    "owner_user_id": "720e76fa-1111-2222-3333-444455556666",
    "settings": {},
    "created_at": "2024-05-01T12:00:00Z",
    "updated_at": "2024-05-01T12:00:00Z"
  }
]
```

Creating a workspace:

```bash
POST /admin/workspaces/123e4567-e89b-12d3-a456-426614174000
Content-Type: application/json

{ "name": "Demo", "slug": "demo" }
```

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Demo",
  "slug": "demo",
  "owner_user_id": "720e76fa-1111-2222-3333-444455556666",
  "settings": {},
  "created_at": "2024-05-02T09:00:00Z",
  "updated_at": "2024-05-02T09:00:00Z"
}
```

### Content

All content routes expect `workspace_id` as a query parameter.

- `GET /admin/nodes` – dashboard with counts of drafts, reviews and published
  items.
- `GET /admin/nodes/all` – list nodes with optional filters
  (`node_type`, `status`, `tag`).
- `POST /admin/nodes/{type}` – create a new item of a given `type`.
- `GET /admin/nodes/{type}/{id}` – fetch a single node item.
- `PATCH /admin/nodes/{type}/{id}` – update an item.
- `POST /admin/nodes/{type}/{id}/publish` – mark the item as published.
- `POST /admin/nodes/{type}/{id}/validate` – run validators and return a
  report.

Example listing and creation:

```bash
GET /admin/nodes/all?workspace_id=8b112b04-1769-44ef-abc6-3c7ce7c8de4e&node_type=article
```

```json
{
  "items": [
    {
      "id": "42",
      "node_type": "article",
      "title": "Hello world",
      "status": "draft",
      "tags": []
    }
  ],
  "total": 1
}
```

```bash
POST /admin/content/article?workspace_id=8b112b04-1769-44ef-abc6-3c7ce7c8de4e
Content-Type: application/json

{ "title": "Hello world", "slug": "hello-world" }
```

```json
{
  "id": "42",
  "content_type": "article",
  "title": "Hello world",
  "status": "draft",
  "workspace_id": "8b112b04-1769-44ef-abc6-3c7ce7c8de4e"
}
```

Publishing:

```bash
POST /admin/content/article/42/publish?workspace_id=8b112b04-1769-44ef-abc6-3c7ce7c8de4e
```

```json
{ "status": "published" }
```

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

