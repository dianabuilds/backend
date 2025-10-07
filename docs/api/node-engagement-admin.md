# Admin Node Engagement API

## Authentication and Headers
- Session cookies and CSRF header (`X-CSRF-Token`) are required.
- Admin endpoints additionally require `X-Admin-Key`.
- Content type: `application/json`.

## Views
### POST `/v1/nodes/{id}/views`
Registers node views.

Request body:
```json
{
  "amount": 1,
  "fingerprint": "device-hash",
  "at": "2025-10-02T12:00:00Z"
}
```

Response:
```json
{
  "id": 123,
  "views_count": 15
}
```

### GET `/v1/nodes/{id}/views`
Returns totals and daily buckets.

Query params: `limit` (1-90), `offset` (>=0).

Response:
```json
{
  "id": 123,
  "total": 15,
  "buckets": [
    {"node_id": 123, "bucket_date": "2025-10-01", "views": 10},
    {"node_id": 123, "bucket_date": "2025-09-30", "views": 5}
  ]
}
```

## Reactions
### POST `/v1/nodes/{id}/reactions/like`
Adds like for current user and returns summary.

### DELETE `/v1/nodes/{id}/reactions/like`
Removes like.

### GET `/v1/nodes/{id}/reactions`
Returns totals and user reaction (if authenticated).

## Comments
### GET `/v1/nodes/{id}/comments`
Query params: `parentId`, `limit` (<=200), `offset`, `includeDeleted` (requires node author or moderator).

Response items expose `id`, `node_id`, `author_id`, `parent_comment_id`, `depth`, `content`, `status`, `metadata`, `created_at`, `updated_at`.

### POST `/v1/nodes/{id}/comments`
Body: `content` (string), `parent_id` (optional), `metadata` (object).

### DELETE `/v1/nodes/comments/{comment_id}`
Query params: `hard`, `reason`. Allowed for comment author, node author, or moderator.

### PATCH `/v1/nodes/comments/{comment_id}/status`
Body: `{ "status": "hidden", "reason": "spam" }`. Moderator only.

### POST `/v1/nodes/{id}/comments/lock`
Body: `{ "locked": true, "reason": "maintenance" }`. Node author or moderator.

### POST `/v1/nodes/{id}/comments/disable`
Body: `{ "disabled": true, "reason": "freeze" }`. Node author or moderator.

### Ban management
- POST `/v1/nodes/{id}/comments/ban` - `{ "target_user_id": "uuid", "reason": "abuse" }`.
- DELETE `/v1/nodes/{id}/comments/ban/{user_id}`.
- GET `/v1/nodes/{id}/comments/bans` - node author or moderator.

Responses include `node_id`, `target_user_id`, `set_by`, `reason`, `created_at`.

## Node card fields
`GET /v1/nodes/{id}` already exposes `views_count`, `reactions_like_count`, `comments_disabled`, `comments_locked_by`, `comments_locked_at`.

## Error codes
- 400: `amount_invalid`, `fingerprint_invalid`, `timestamp_invalid`, `content_required`, `parent_id_invalid`, `metadata_invalid`, `target_user_id_required`.
- 401: `unauthorized`.
- 403: `forbidden`, `insufficient_role`.

## Tests and references
- `apps/backend/app/tests/test_nodes_api.py::test_node_engagement_endpoints` for end-to-end flow.
- Local smoke: `poetry run uvicorn apps.backend.app.api_gateway.main:app --reload` and call endpoints with Postman or HTTPie.

## Admin Endpoints

### GET `/v1/admin/nodes/{id}/engagement`
Returns a consolidated summary for the node card. Response includes node metadata, cumulative counters (`views_count`, reactions), comment status breakdown, lock/disable state, and helper links per node.

```json
{
  "id": "42",
  "views_count": 120,
  "reactions": {"like": 18},
  "comments": {
    "total": 25,
    "by_status": {"published": 20, "pending": 2, "hidden": 1, "deleted": 2, "blocked": 0},
    "disabled": false,
    "locked": false,
    "locked_by": null,
    "locked_at": null,
    "bans_count": 1
  },
  "links": {
    "moderation": "/v1/admin/nodes/42/moderation",
    "comments": "/v1/admin/nodes/42/comments",
    "analytics": "/v1/admin/nodes/42/analytics",
    "bans": "/v1/admin/nodes/42/comment-bans"
  }
}
```

### GET `/v1/admin/nodes/{id}/comments`
Lists comments for the admin UI. Query params:

- `view`: `roots` (default), `children`, `all`, or `thread`.
- `parentId`: comment id used with `children`/`thread`.
- `status`: one or more values (`pending`, `published`, `hidden`, `deleted`, `blocked`).
- `authorId`, `createdFrom`, `createdTo`, `search`.
- `includeDeleted` (default `true`).
- `limit`/`offset` and `order` (`desc` by default).

Response contains `items`, per-status summary, pagination metadata, and echoed filters. Each comment carries `metadata`/`history`, `children_count`, and timestamps.

### POST `/v1/admin/nodes/{id}/comments/lock`
Locks or unlocks comments for a node.

Body:
```json
{"locked": true, "reason": "maintenance"}
```

Response provides the new lock flag and updated comment summary. Unlock by sending `{"locked": false}`.

### POST `/v1/admin/nodes/{id}/comments/disable`
Enable/disable comments globally.

Body:
```json
{"disabled": true, "reason": "cooldown"}
```

Response mirrors lock endpoint.

### POST `/v1/admin/nodes/comments/{comment_id}/status`
Changes moderation status for a single comment (`published`, `hidden`, `pending`, `blocked`, `deleted`). Optional `reason` is recorded in the comment history.

Returns the updated comment payload and refreshed summary.

### DELETE `/v1/admin/nodes/comments/{comment_id}`
Soft deletes by default; pass `hard=true` to remove permanently. Optional query param `reason` is persisted in history.

### Comment Ban Management

- `GET /v1/admin/nodes/{id}/comment-bans`  list active bans (target id, set_by, reason, created_at).
- `POST /v1/admin/nodes/{id}/comment-bans`  upsert a ban: `{ "target_user_id": "uuid", "reason": "spam" }`.
- `DELETE /v1/admin/nodes/{id}/comment-bans/{user_id}`  remove a ban.

All ban endpoints require valid UUIDs for `target_user_id` and the acting admin.

### GET `/v1/admin/nodes/{id}/analytics`
Returns day buckets for views, reaction totals, and comment distribution.

Query params:
- `start`, `end`: ISO timestamps (UTC).
- `limit`: day buckets to return (default `30`, max `365`).
- `format`: set to `csv` to receive a downloadable dataset (`bucket_date,views,total_likes,total_comments`).

JSON response:
```json
{
  "id": "42",
  "range": {"start": "2025-09-01T00:00:00Z", "end": "2025-09-30T23:59:59Z"},
  "views": {
    "total": 120,
    "buckets": [{"bucket_date": "2025-09-30", "views": 6}],
    "last_updated_at": "2025-09-30T15:05:00Z"
  },
  "reactions": {"totals": {"like": 18}, "last_reaction_at": "2025-09-30T12:00:00Z"},
  "comments": {"total": 25, "by_status": {"published": 20, "pending": 2, "hidden": 1, "deleted": 2, "blocked": 0}},
  "delay": {"seconds": 120, "calculated_at": "2025-09-30T15:05:10Z", "latest_at": "2025-09-30T15:03:10Z"}
}
```

> Tip: supply `X-Actor-Id` with an admin UUID to persist audit trails. When omitted, the system uses a neutral system actor id.
