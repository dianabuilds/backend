# Home Composer

This module assembles the payload for the public `/v1/public/home` endpoint. It expands
the blocks stored in `HomeConfig` into fully hydrated cards using manual and automatic
sources.

## Components

- `HomeComposer` orchestrates block traversal, delegates to data source strategies and
  writes the result to a cache port.
- `ManualSource` loads items by explicit identifiers and preserves the requested order.
- `AutoSource` applies tag/order/limit filters with a strict upper bound (`limit ? 12`).
- `NodeDataService`, `QuestDataService` and `DevBlogDataService` expose a minimal
  asynchronous interface for fetching cards. Concrete implementations can wrap existing
  domain services or repositories.
- `HomeCache` is a protocol that allows plugging Redis or the provided
  `InMemoryHomeCache` for tests.

## Behaviour Highlights

- Disabled blocks or blocks without data sources are skipped and reported through the
  `fallbacks` collection.
- Manual blocks log missing identifiers without failing the whole response.
- Automatic blocks enforce a timeout and limit to shield the database from expensive
  scans.
- Errors and timeouts result in a fallback entry so the public response stays clean.

See `tests/domains/product/content/test_home_composer.py` for usage examples.
