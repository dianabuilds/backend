# workers/

Background workers for the backend:

- `events_worker.run()` – dispatches domain events from Redis Streams.
- `schedule_worker.run()` – periodic scheduler for content publish/unpublish.
- `notifications_worker.run()` – runs the notifications broadcast queue via `packages.worker`.

## CLI

Use the unified entrypoint:

```
python -m apps.backend.workers events
python -m apps.backend.workers scheduler --interval 45
python -m apps.backend.workers notifications -- --once
```

The helper caches the DI container, so repeated runs reuse the same bootstrap.
