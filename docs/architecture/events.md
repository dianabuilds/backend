# Events & Integrations

This document summarizes the standardized event topics, payload structures, and publishing approach across domains.

## Patterns

- System event bus (`app.domains.system.events.bus`) centralizes listener registration, handler retries (up to 3 attempts), and metrics.
- Outbound integrations use the Transactional Outbox via the System facade `app.domains.system.platform.outbox.emit`.
- Deduplication keys are applied where sensible to prevent duplicates on retries.
- JSON Schemas are committed under each domain at `events/specs/*.json` and compiled in CI.

## Topics

- `event.notification.created.v1`
  - Publisher: `app.domains.notifications.events.publisher.publish_notification_created`
  - Dedup: `notification:{id}`
  - Schema: `apps/backend/app/domains/notifications/events/specs/notification.created.v1.json`

- `event.navigation.cache.invalidated.v1`
  - Publisher: `app.domains.navigation.events.publisher.publish_nav_cache_invalidated`
  - Dedup: `navinvalidate:{scope}:{user_id|all}:{node_id}:{slug}:{reason}`
  - Schema: `apps/backend/app/domains/navigation/events/specs/navigation.cache.invalidated.v1.json`

- `event.profile.updated.v1`
  - Publisher: `app.domains.profile.events.publisher.publish_profile_updated`
  - Dedup: `profile:{id|user_id}:{md5(profile)}`
  - Schema: `apps/backend/app/domains/profile/events/specs/profile.updated.v1.json`

## Bus Registration

All domain listeners are subscribed from `system/events/bus.register_handlers()`. Domain modules should not self-register listeners on import.

## Outbox Facade Rule

Domains must not import `app.providers.outbox` directly. Use `app.domains.system.platform.outbox.emit` only. Enforced by import-linter in CI (`backend/importlinter.ini`).

