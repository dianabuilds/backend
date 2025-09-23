# ADR 0002: Node Embedding Integration

- Status: Approved
- Date: 2025-09-21
- Authors: Team Navigation
- Tags: navigation, embeddings, pgvector, frontend

## Context

The transition engine now relies on semantic similarity (vectors) to score and diversify navigation candidates. The current backend stores no embedding data for nodes, so the scoring pipeline falls back to tag heuristics and random hops. We also need deterministic explainability (`tag_sim`, `diversity_bonus`) and ANN retrieval to fulfill ADR 0001. The environment already exposes AIML API credentials for embeddings, and pgvector is available in the database. The goal is to add embeddings to nodes, recompute them on content changes, and expose them to the navigation pipeline and UI in one end-to-end iteration.

## Decision

Adopt pgvector-backed embeddings for product nodes. Embeddings are generated online through the AIML API client inside `NodeService` for writes (`create`, `update`, `update_tags`). They are stored in a `vector(1536)` column and exposed through DTO/view models. Navigation's candidate pipeline uses cosine similarity and ANN retrieval via pgvector. Admin/UI paths expose the embedding status in diagnostics but do not display vectors directly.

### Data model

- PostgreSQL: `CREATE EXTENSION IF NOT EXISTS vector;`
- Column `nodes.embedding vector(1536)`; ivfflat index `nodes_embedding_ivfflat`. Empty tables allow recreation without migrations history rewrites; existing rows are wiped before migration.
- DTOs (`NodeDTO`, `NodeView`) include `embedding: list[float] | None`.
- Repo adapters read/write embeddings for CRUD and fallback SELECTs.

### Embedding client

- New module `domains/product/nodes/application/embedding.py` with `EmbeddingClient` wrapping `httpx.AsyncClient`.
- Configured by `Settings` (`EMBEDDING_PROVIDER`, `EMBEDDING_API_BASE`, `EMBEDDING_MODEL`, `EMBEDDING_API_KEY`, `EMBEDDING_DIM`).
- Retries (3), timeout (2s connect/10s read), exponential backoff. On failure returns `None` and logs warning (`embedding_generation_failed`).
- Flag `embedding_enabled` in settings to short-circuit all embedding calls when disabled.

### NodeService & API

- Inject `EmbeddingClient` through DI (`wires.py`).
- `_to_view` helper returns `NodeView` with embedding.
- `_prepare_embedding_text` builds prompt text from title, canonicalized tags, stripped HTML; `_compute_embedding_vector` calls client when flag enabled.
- `create`: await `_compute_embedding_vector`; pass vector to repo.
- `update`: recompute embedding if `title`, `tags`, or `content_html` changed; update repo with new vector (partial updates keep previous value when `None`).
- `update_tags`: make async, recompute embedding after tag change, persist via repo.
- API handlers (`create_node`, `patch_node`, `set_tags`) remain synchronous to clients but call new async service methods; they also return `embedding` field in responses for admin tooling.
- CLI script `apps/backend/scripts/recompute_embeddings.py` to recompute per batch (for maintenance/testing).

### Navigation pipeline

- `NavigationService` loads embeddings from context; compute session query vector (
  `0.6 origin + 0.2 mean(lastN) + 0.2 prefs`).
- `compass` provider queries pgvector ANN (`ORDER BY embedding <-> :query LIMIT K`). Fallback to existing heuristics if no embeddings exist.
- `tag_sim` becomes cosine similarity between origin/query vectors and candidate embedding (normalize vectors before dot product). Factor surfaces in `reason` payload (e.g., `tag_sim=0.72`).
- `TransitionCandidate` retains embedding only internally (not in API). The selection stage uses weighted scores from embeddings; fallback to old scoring if embeddings missing.
- Feature flag `embedding_enabled` toggles embedding-based scoring and retrieval (fallback to tag heuristics when off).

### Frontend

- Admin UI: update node forms to submit `content_html`, tags, etc. Node list surfaces embedding status badges (“Ready/Pending/Disabled/Error”) and aggregates outstanding recomputes. Ensure `/v1/navigation/next` consumer (if any internal admin tool) adapts to new response fields (`ui_slots_requested`, `decision.candidates[].reason` etc.) introduced earlier.
- No new user-facing UI changes required, but internal dashboards should expose telemetry from the API (pool size, embedding usage).

## Consequences

- **Positive**: improved ranking quality, ability to reuse ADR 0001 pipeline, deterministic explainability, direct path to ANN retrieval.
- **Trade-offs**: writes incur embedding generation latency (~100–300 ms). Need resilience to API outages. Without queue, spikes in writes may stress the embedding API (mitigated with flag and retries).
- **Operational**: thin wrappers around pgvector rely on proper extension availability; database migrations must precede app rollout.

## Implementation Plan

1. **Migrations**
   - Create SQL `008_nodes_embedding.sql` with extension, column, IVFFLAT index.
   - Alembic revision `0015_nodes_embedding.py` executes SQL; downgrade drops column.
2. **DTO & Repo updates**
   - Extend `NodeDTO`/`NodeView` with `embedding`.
   - Update memory and SQL repos for get/list/create/update to map the column.
3. **Embedding client**
   - Implement `EmbeddingClient` using `httpx.AsyncClient`.
   - Add configuration fields to `Settings` (read from existing env vars) and `embedding_enabled` flag.
4. **NodeService**
   - Introduce `_prepare_embedding_text` and `_compute_embedding_vector` helpers.
   - Inject client; modify `create`, `update`, `update_tags` to recompute embeddings.
   - Update API handlers (async) and ensure responses include embeddings (for observability).
5. **Navigation**
   - Store candidate embeddings in pipeline, calculate cosine similarity, update scoring weights.
   - Implement pgvector ANN retrieval for `compass` provider.
   - Add flag fallback and integration tests.
6. **Frontend/Admin**
   - Adjust admin tooling to tolerate new response fields and optionally display diagnostic badges.
7. **Testing**
   - Unit tests for `EmbeddingClient`, NodeService (mock embedding), navigation scoring (cosine), pipeline fallback.
   - Integration tests for node API (embedding generated, updated after tag change).
   - Smoke test for `/v1/navigation/next` verifying reason payload includes `tag_sim` and new fields.
8. **CLI & ops**
   - Implement `recompute_embeddings.py` (batch update script).
   - Logging/metrics: expose counters for embedding success/failures, ANN utilization.
   - Document flag/monitoring expectations.
9. **Deployment**
   - Apply migrations (extension + column/index) with empty table or after truncation.
   - Ship backend changes and run smoke tests.
   - Monitor embedding API calls, ANN query latency, and navigation metrics.

## Observability & Metrics

- Structured logs capture embedding requests, response latency, provider codes, and fallback paths for traceability. CLI recompute emits `embedding_recompute_summary` totals per run.
- Metrics: `node_embedding_requests_total`, `node_embedding_latency_ms`, and `navigation_embedding_queries_total` with status dimensions; counters for CLI processed nodes and ANN fallback rate.
- Alerts: embedding failure ratio >5% over 10 minutes, ANN latency p95 >50 ms, or embedding_enabled flag disabled in production for >30 minutes.
- Feature flag instrumentation: track dark launches with per-tenant overrides before full rollout.

## Testing & Readiness

### Acceptance

- [ ] Node create/update returns embedding vectors when the feature flag is enabled and hides them when disabled.
- [ ] Tag updates recompute embeddings and persist new vectors without duplicating metadata.
- [ ] Navigation pipeline blends embeddings into scoring and falls back to heuristics when vectors are missing.
- [ ] Admin diagnostics surface embedding status codes for nodes queried through the API.

### Test plan

- Unit: EmbeddingClient retries/backoff, NodeService recompute rules, cosine similarity math, ANN query builders.
- Integration: end-to-end node create/update/list flows with embedded data, navigation request verifying tag_sim reasons, CLI recompute run against fixture dataset.
- Performance: measure node write latency with embeddings (target <350 ms p95) and ANN query regression compared to baseline.
- Manual: run recompute script in staging, simulate embedding API outage, verify admin panel badges.

## Risks & Mitigations

- Embedding provider outage: guard with feature flag, cached vectors, and explicit alerts; add runbook for manual disable.
- Model drift across re-training: version embeddings via metadata and schedule recompute when provider model changes.
- Latency regression on writes: measure continuously and consider background queues if p95 exceeds target.
- Data governance: ensure text sent to provider respects tenant privacy redactions and audit logs include who triggered recompute.

## Alternatives Considered

- Queue-based asynchronous embedding generation (delayed but isolates write latency); deferred until we validate the synchronous path.
- Managed vector store (e.g., Pinecone, Astra) offering turnkey ANN; rejected in favour of pgvector to limit dependencies.
- Client-side caching of embeddings in navigation service; discarded to keep a single source of truth in the database.

## Follow-up Work

- Add background worker/queue once the synchronous path is validated and throughput needs increase.
- Build offline evaluation harness to compare embedding quality against heuristic scoring.
- Extend embeddings to related entities (topics, trails) and align navigation pipeline.
- Wire new Prometheus series into dashboards/alerts and document the CLI recompute runbook.
- Document operational runbooks, dashboards, and weekly quality review cadence.

## Open Questions

### Recompute cadence when the model or preprocessing changes

- Version the embedding pipeline with `EMB_PIPELINE=MAJOR.MINOR.PATCH`.
- MAJOR bumps (model/architecture/dimensionality) trigger a full recompute.
- MINOR bumps (preprocessing changes) allow incremental recompute but must converge to full coverage.
- PATCH bumps (bug fixes that do not alter vectors) skip recompute.
- Triggers: tagged pipeline commits (`emb/*` with version bump), preprocessing flag changes, or new model hashes in the artifact registry.
- Process: create a blue/green index `vec_index_v<version>`, rebuild embeddings by priority tiers, cut over the alias after >=95% coverage and ranking checks, keep the old index warm for 7-14 days for rollback.

### Embedding versioning for A/B evaluation and rollbacks

- Persist multiple embedding versions per content item:

  ```sql
  content_embeddings(
    content_id uuid,
    emb_version text,
    preproc_hash bytea,
    vector vector(1536),
    quality_score real,
    created_at timestamptz,
    primary key (content_id, emb_version)
  )
  ```
- Maintain at least `current` and `candidate` indexes; support A/B (bucket by user id) and shadow modes (100% mirrored traffic without exposing results).
- Rollbacks flip the alias back to the previous version and disable the candidate flag in a single operation.

### Tenant API keys and rate limiting

- Issue dedicated credentials per tenant/environment; store key ids in `tenant_api_keys` and keep secrets in the provider or KMS.
- Apply hierarchical token buckets (tenant, tenant+model, tenant+endpoint) with configurable burst/rate, e.g., burst 60 and 120/min per model.
- Use weighted fair queuing on workers plus max in-flight per tenant (e.g., 8) to prevent noisy-neighbour pressure.
- Enforce monthly budget caps: when usage approaches the limit, throttle aggressively or pause non-critical calls.
- Support dual-key rotation (90-day schedule or incident-driven) with seamless cutover.

### Cost ownership and thresholds

- RecSys/Search team owns usage forecasts, model choices, and quality SLOs.
- SRE/Platform manages provider SLAs, alerting, and emergency feature switches.
- FinOps/PM sets monthly budgets and approves increases or stop-gaps.
- Budget alerts: 80% (heads-up), 90% (enable moderate throttling, pause experiments), 100% (severe throttling, halt background recompute).
- Monitor anomalies: >30% day-over-day cost per request growth, provider 429/5xx spikes, latency breaching p95 SLO.
- Dashboards: cost per 1k embeddings, QPS per tenant, success/timeout rates, token usage per minute, A/B traffic split, recompute coverage.
## Status

Implementation in progress; queue/worker integration will follow once the synchronous flow is stable.



