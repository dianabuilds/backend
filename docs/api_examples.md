# API Examples

Quick examples for interacting with workspace-aware endpoints.

## Error format

All API errors follow a unified structure:

```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Error description"
  }
}
```

Clients can rely on the ``code`` field for machine readable handling of
different error scenarios.

## HTTPie

### Versioned requests

```bash
# v1 – list workspaces using alt_id identifiers
http GET :8000/v1/workspaces

# v2 – list workspaces using numeric ids
http GET :8000/v2/workspaces

# v1 – get node by alt_id
http GET :8000/v1/nodes/123e4567-e89b-12d3-a456-426614174000

# v2 – get node by id
http GET :8000/v2/nodes/42
```

### Pagination

```bash
# Fetch first page
http GET :8000/v2/workspaces/123e4567-e89b-12d3-a456-426614174000/nodes?limit=2

# Follow the next link
http GET :8000/v2/workspaces/123e4567-e89b-12d3-a456-426614174000/nodes?cursor=eyJrIjoiMTIzIn0=
```

Typical responses include a ``next`` link:

```json
{
  "items": [],
  "next": "/v2/workspaces/123e4567-e89b-12d3-a456-426614174000/nodes?cursor=eyJrIjoiMTIzIn0="
}
```

## Postman

Import the `docs/postman_collection.json` file in Postman and set the `baseUrl`, `workspace_id` and optional `cursor` variables. The collection contains requests for listing workspaces, creating a workspace and querying nodes within a workspace with pagination.
