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

```bash
# List workspaces
http GET :8000/admin/workspaces

# Create a workspace
http POST :8000/admin/workspaces/123e4567-e89b-12d3-a456-426614174000 name=Demo slug=demo

# List nodes within a workspace
http GET :8000/admin/nodes/all workspace_id==123e4567-e89b-12d3-a456-426614174000 node_type==article
```

## Postman

Import the `docs/postman_collection.json` file in Postman and set the `baseUrl` and `workspace_id` variables. The collection contains requests for listing workspaces, creating a workspace and querying nodes within a workspace.
