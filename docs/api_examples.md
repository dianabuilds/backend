# API Examples

Quick examples for interacting with account-aware endpoints.

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
different error scenarios. Supported mappings are:

- 400 → ``BAD_REQUEST``
- 401 → ``AUTH_REQUIRED``
- 403 → ``FORBIDDEN``
- 404 → ``NOT_FOUND``
- 405 → ``METHOD_NOT_ALLOWED``
- 409 → ``CONFLICT``
- 422 → ``VALIDATION_ERROR``
- 429 → ``RATE_LIMITED``

## HTTPie

### Versioned requests

```bash
# list accounts
http GET :8000/accounts limit==5

# get node by id (UUID)
http GET :8000/nodes/d6f5b4e2-1c02-4b7a-a1f0-b6b0b7a9f6ef
```

### Pagination

```bash
# Fetch first page
http GET :8000/v2/accounts/123e4567-e89b-12d3-a456-426614174000/nodes?limit=2

# Follow the next link
http GET :8000/v2/accounts/123e4567-e89b-12d3-a456-426614174000/nodes?cursor=eyJrIjoiMTIzIn0=
```

Typical responses include a ``next`` link:

```json
{
  "items": [],
  "next": "/v2/accounts/123e4567-e89b-12d3-a456-426614174000/nodes?cursor=eyJrIjoiMTIzIn0="
}
```

## Postman

Import the `docs/postman_collection.json` file in Postman and set the `baseUrl`, `account_id` and optional `cursor` variables. The collection contains requests for listing accounts, creating an account and querying nodes within an account with pagination.
