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
- `POST /admin/workspaces/{workspace_id}/nodes/{type}/{id}/validate` returns no blocking issues.
- Cover media and other mandatory fields are set.
- Peer review is completed (`in_review`).
- Publish via `POST /admin/workspaces/{workspace_id}/nodes/{type}/{id}/publish` and verify in the
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

### Nodes

Most node routes are namespaced by workspace and use the path prefix
`/admin/workspaces/{workspace_id}`.

Common endpoints:

| Operation | Path |
|-----------|------|
| List nodes | `/admin/workspaces/{id}/nodes` |
| List all nodes | `/admin/workspaces/{id}/nodes/all` |
| Create node | `POST /admin/workspaces/{id}/nodes/{type}` |
| Get node | `/admin/workspaces/{id}/nodes/{type}/{id}` |
| Update node | `/admin/workspaces/{id}/nodes/{type}/{id}` |
| Publish node | `/admin/workspaces/{id}/nodes/{type}/{id}/publish` |
| Validate node | `/admin/workspaces/{id}/nodes/{type}/{id}/validate` |

- `GET /admin/workspaces/{id}/nodes` – dashboard with counts of drafts, reviews
  and published items.
- `GET /admin/workspaces/{id}/nodes/all` – list nodes with optional filters
  (`node_type`, `status`).
- `POST /admin/workspaces/{id}/nodes/{type}` – create a new item of a given
  `type`.
- `GET /admin/workspaces/{id}/nodes/{type}/{id}` – fetch a single node item.
- `PATCH /admin/workspaces/{id}/nodes/{type}/{id}` – update an item.
- `POST /admin/workspaces/{id}/nodes/{type}/{id}/publish` – mark the item as
  published.
- `POST /admin/workspaces/{id}/nodes/{type}/{id}/validate` – run validators and
  return a report.

Identifiers in these endpoints are **UUIDs** of the corresponding ``NodeItem``.
A numeric ``nodes.id`` is accepted for backward compatibility but clients
should migrate to the UUID form.

Example listing and creation:

```bash
GET /admin/workspaces/8b112b04-1769-44ef-abc6-3c7ce7c8de4e/nodes/all?node_type=article
```

```json
{
  "items": [
    {
      "id": "d6f5b4e2-1c02-4b7a-a1f0-b6b0b7a9f6ef",
      "node_type": "article",
      "title": "Hello world",
      "status": "draft"
    }
  ],
  "total": 1
}
```

```bash
POST /admin/workspaces/8b112b04-1769-44ef-abc6-3c7ce7c8de4e/nodes/article
Content-Type: application/json

{ "title": "Hello world", "slug": "hello-world" }
```

```json
{
  "id": "d6f5b4e2-1c02-4b7a-a1f0-b6b0b7a9f6ef",
  "node_type": "article",
  "title": "Hello world",
  "status": "draft",
  "workspace_id": "8b112b04-1769-44ef-abc6-3c7ce7c8de4e"
}
```

Updating content:

```bash
PATCH /admin/workspaces/8b112b04-1769-44ef-abc6-3c7ce7c8de4e/nodes/article/d6f5b4e2-1c02-4b7a-a1f0-b6b0b7a9f6ef
Content-Type: application/json

{ "content": { "time": 0, "blocks": [], "version": "2.30.7" } }
```

Legacy `nodes` field is rejected with HTTP 422.
Publishing:

```bash
POST /admin/workspaces/8b112b04-1769-44ef-abc6-3c7ce7c8de4e/nodes/article/d6f5b4e2-1c02-4b7a-a1f0-b6b0b7a9f6ef/publish
```

```json
{ "status": "published" }
```

## Front‑end flows

The admin UI communicates with these routes:

- **Workspace selection** – `WorkspaceSelector` fetches `/admin/workspaces` and
  stores the chosen ID in session storage. The API client automatically
  prefixes requests with `/admin/workspaces/{id}`.
- **Dashboard** – `ContentDashboard` calls `/admin/workspaces/{id}/nodes` to show counts of
  drafts, reviews and published items.
- **Content list** – `ContentAll` uses `/admin/workspaces/{id}/nodes/all` with filters for type
  and status.
- **Tag management** – `TagMerge` and other components operate on tags using the
  standard admin tag endpoints.

