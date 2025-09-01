# API Versioning

The API now uses numeric `id` identifiers exclusively. Earlier UUID-based `alt_id`
fields have been removed and are no longer supported.

## Migration guidance

Clients that previously relied on `alt_id` should migrate to numeric identifiers
by fetching node records and storing the `id` field. All endpoints expect the
numeric `id` and return it in responses.
