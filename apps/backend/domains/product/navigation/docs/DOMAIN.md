Navigation domain: compute next node for user based on simple strategies.

Dependency: NodesPort provided by container wrapper.

## Error Handling

- Provider weights and mode setup live in `domains.product.navigation.config`, making ANN tuning explicit and testable.
- Embedding lookups catch SQL/runtime/provider errors, emit `nav_embedding_search_failed`, and downtick metrics via a labeled counter (`used`, `empty`, `error`).
- Relaxation fallback paths (`nav_relaxation_*`, `nav_candidates_fallback`) produce structured logs with mode, limit state, and pool size, so SREs can trace why random or empty results were returned.

