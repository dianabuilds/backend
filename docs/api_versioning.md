# API Versioning

The API is available in two versions:

- **/v1** – uses `alt_id` (UUID) as the primary identifier.
- **/v2** – introduces numeric `id` while still accepting `alt_id` for compatibility.

## Identifier differences

| Version | Path pattern | Identifier type |
|---------|--------------|-----------------|
| `/v1`   | `/v1/nodes/{alt_id}` | `alt_id` (UUID) |
| `/v2`   | `/v2/nodes/{id}`     | numeric `id`; `alt_id` accepted but deprecated |

## alt_id support timeline

`alt_id` will remain supported until **31 December 2025**. After that date, all clients must use numeric `id` exclusively.

## Migration steps

1. Fetch nodes using `/v1` and store both `id` and `altId`.
2. Update client logic to call `/v2` endpoints with the numeric `id`.
3. Remove usage of `alt_id` before the deprecation date.
