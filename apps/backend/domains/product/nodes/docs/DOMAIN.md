Nodes domain: read/update node tags, simple visibility rules.

Adapters: in-memory repo, tag catalog, outbox, usage projection for tag counters.

## Error Handling

- Admin HTTP endpoints route event publication through `_safe_publish` via `_emit_admin_activity`, ensuring outbox logging and retry semantics.
- SQL errors are mapped to explicit `HTTPException` responses (`404`, `400`, `500`) and logged with structured extras, so operators can correlate actor, node_id, and action.
- Audit trails use `AuditService.log`; failures are captured and logged without interrupting the user flow.

