# ADR 0001: Transition Engine Core Model

- Status: Accepted
- Date: 2025-09-21
- Authors: TBD
- Tags: navigation, recommendations, pipelines

## Context

Navigation between content nodes evolved ad hoc through multiple prototypes. The system lacks a shared definition of the transition state, mixes anti-loop logic with scoring, and exposes inconsistent behaviour across modes (normal, near-limit, lite, premium). UI teams report that buttons shift unexpectedly when quotas change, and backend telemetry cannot replay decisions deterministically. We need a consolidated transition engine that keeps the experience predictable, auditable, and extensible.

## Decision

We introduce a single transition engine contract centred on a TransitionContext and a deterministic pipeline. All compass modes consume the same stages, with the mode matrix controlling tuned parameters for providers, diversity, stochasticity, and UI slot counts.

### TransitionContext

TransitionContext captures the minimum state required to choose the next node and to replay the decision:

- session_id, optional user_id (pseudonymous)
- origin_node_id and route_window (last 6 nodes)
- limit_state (normal, near_limit, exceeded_lite) and premium_level
- requested_ui_slots
- policies_hash referencing the active NavigationPolicy set
- cache_seed providing deterministic selection
- timestamps for TTL management

Contexts are cached for five minutes on the key `(user_or_session, origin_node_id, limit_state, mode)` so UI slots remain stable while quotas and policies are respected. Every decision persists the context reference plus the ranked candidates (TransitionDecision) for observability and replay.

TransitionDecision stores `ui_slots_requested`, `ui_slots_granted`, `curated_blocked_reason`, `empty_pool_reason`, factor payloads, and the selected node id. Analytics clients consume these fields directly; they are not optional in the schema.

### Pipeline Stages

The engine always executes the same ordered stages:

1. **CandidateProviders** gather data from curated (trails, collections), compass retrieval (ANN neighbours), echo continuation, and policy-aware random hops.
2. **EligibilityFilter** applies visibility, premium, age/NSFW, blocked tags, and provider caps before scoring.
3. **DiversityGuard** enforces anti-loop (2-cycle, last 6 nodes) and anti-bubble constraints (author and tag cluster thresholds, orthogonal hop requests).
4. **Scorer** calculates weighted scores and applies curated boosts prior to selection.
5. **Selector** grants the final number of UI slots (potentially less than requested) using `softmax(score / t)` across the surviving candidates; `t` comes from the active mode.
6. **Formatter** produces badges, explanations, and telemetry payloads.
7. **Persistence** records the TransitionDecision, emits EchoEvent, and logs metrics.

Each stage exposes metrics (pool_size, filtered counts, latency) and can be toggled by feature flags for rollouts.

### Mode Matrix

Compass behaviour is described by a small set of modes with explicit parameter overrides:

| Mode       | Providers                      | K base | t    | epsilon | Diversity guard parameters               | UI slots (free/premium/premium+) | Notes                      |
|------------|--------------------------------|--------|------|---------|------------------------------------------|----------------------------------|----------------------------|
| normal     | curated, compass, echo, random | 48     | 0.30 | 0.05    | authors <= 3, tag clusters <= 3          | 3 / 3 / 4                       | Default session state      |
| echo_boost | curated, compass, echo         | 48     | 0.25 | 0.00    | same thresholds, echo weight +30%        | 3 / 3 / 4                       | User initiated follow-up   |
| discover   | curated, compass, random       | 64     | 0.50 | 0.15    | tag clusters <= 2, forced hop every 4    | 3 / 3 / 4 (Premium+ unlimited)  | Premium+ exploratory mode  |
| editorial  | curated, compass               | 32     | 0.10 | 0.00    | penalties only, no forced hops           | 3 / 3 / 4                       | Story driven views         |
| near_limit | curated, compass, echo         | 36     | 0.20 | 0.00    | same thresholds, random disabled         | 3 / 3 / 4                       | Quota near exhaustion      |
| lite       | curated, compass               | 16     | 0.15 | 0.00    | penalties only, random and echo disabled | 2 / 2 / 2                       | Limit state exceeded       |

During `limit_state=exceeded_lite` every tier receives two slots. Premium and Premium+ users may trigger an emergency reset (one call per 10 minutes) to temporarily treat the next request as `limit_state=normal`.

### Empty Pool Relaxation Ladder

When the provider pool drains after eligibility and diversity checks, the engine relaxes constraints in order:

1. Reduce diversity_penalty strength by one notch.
2. Expand provider K caps by 25% for the current mode.
3. Enable the random provider (skipped if the active mode is lite).
4. If the pool is still empty, return `empty_pool=true`, include fallback suggestions (search, map, last working trail), and log `empty_pool_reason`.

### Caching & Determinism

- cache_seed = hash(user_id|session_id, origin_node_id, limit_state, mode)
- Cache key matches the same tuple; TTL is 5 minutes or until invalidated by new EchoEvent or NavigationPolicy change.
- Selector softmax uses the cache_seed to drive deterministic sampling where randomness is required.

## Rationale

- Explicit context and deterministic selection make UI buttons stable and decisions auditable.
- A shared pipeline removes logic duplication across modes and lets teams reason about stage-specific metrics.
- The mode matrix documents deliberate trade-offs between engagement (higher temperature, additional providers) and quota control (reduced K, zero epsilon) while fixing UI slot expectations.
- Persisting TransitionDecision simplifies debugging, experimentation, and analytics because telemetry can attribute outcomes to concrete factors.
- Clear separation of hard policies (eligibility) and soft diversity penalties allows gradual relaxation without violating safety or quota constraints.

## Consequences

Positive:
- Faster onboarding for new experiences: UI and experiments only switch modes instead of forking logic.
- Replayable decisions unblock investigations into loops, bubbles, or quota regressions.
- Observability and SLOs attach to known stages, supporting automated alerts.

Trade-offs and costs:
- Schema updates required for TransitionContext and TransitionDecision tables plus caching layer alignment.
- Candidate providers must be refactored to respect stage boundaries (for example curated injecting metadata instead of short-circuiting).
- ANN retrieval and diversity guard tuning demand baseline benchmarks to avoid latency regressions.
- Privacy baseline is enforced: pseudonymous user_id only, no raw IP in logs, EchoEvent retention 90 days raw / 1 year aggregates.

## Implementation Notes

1. Create storage models and caching keyed on (user_or_session, origin_node, limit_state, mode); invalidate on policy changes or new EchoEvent.
2. Refactor existing compass code to emit stage metrics and structured factors in key=value form (`reason` keys frozen below).
3. Store mode configuration as data (YAML or feature-flagged settings), log `mode_config_version`, and allow runtime overrides behind ops controls.
4. Update /compass/next to expose ui_slots_requested, ui_slots, mode_applied, served_from_cache, curated_blocked_reason, and emergency_used flags.
5. Extend monitoring dashboards with empty-pool percentage, diversity scores, quota transitions, and SLO alerts at 60 ms (p95) / 120 ms (p99).
6. UI contract: badges limited to {trail, similar, trending, explore, limited, editorial}. `reason` payload keys limited to {curated, tag_sim, echo, fresh, diversity_bonus, policy_penalty}. Localisation dictionary (RU-EN) maintained centrally.
7. Provider overrides (`requested_provider_overrides`) are ignored for production clients and only honoured under an admin feature flag with audit logging.
8. Guest flows identify users as `anon_<hash(session_id)>`, inherit free-tier quotas, and share the same cache TTL and privacy guarantees.

## Operational Controls

- Quota hysteresis: enter near_limit when remaining quota <= 20%; return to normal when >= 30%.
- Emergency reset: Premium tiers may request one emergency per user every 10 minutes; the override applies to the next response only, increments a dedicated rate limiter, sets `emergency_used=true`, and does not accumulate.
- Feature flags: explore_enabled, lite_mode_enabled, premium_emergency_enabled, provider_override_enabled.
- ANN fallback: when the index is cold, rely on cached decisions or curated providers before degrading the response.

## API Contract

### Request

POST /compass/next

```
{
  "origin_node_id": "A123",
  "session_id": "s-98f...",
  "user_id": "u-45b..."?,
  "limit_state": "normal",
  "mode": "normal",
  "ui_slots": 3,
  "premium_level": "free",
  "include_explanations": true,
  "requested_provider_overrides": ["curated","compass"] // honoured only if provider_override_enabled
}
```

### Response

```
{
  "query_id": "q-1ce...",
  "ui_slots_requested": 3,
  "ui_slots": 3,
  "limit_state": "normal",
  "emergency_used": false,
  "decision": {
    "candidates": [
      {"id":"B","badge":"trail","score":0.91,"reason":{"curated":1,"fresh":0.82},"explain":"Next trail step"},
      {"id":"C","badge":"similar","score":0.74,"reason":{"tag_sim":0.71,"echo":0.62,"fresh":0.55},"explain":"Similar topic; readers continued after A"},
      {"id":"D","badge":"explore","score":0.58,"reason":{"diversity_bonus":0.40,"fresh":0.55},"explain":"New branch for diversity"}
    ],
    "curated_blocked_reason": null,
    "empty_pool": false,
    "empty_pool_reason": null,
    "served_from_cache": false
  },
  "pool_size": 37,
  "cache_seed": "f3d1...",
  "t": 0.30,
  "epsilon": 0.05,
  "mode_applied": "normal",
  "telemetry": {"time_ms": 38}
}
```

### Empty pool fallback

If `empty_pool=true`, the response must also contain `fallback_suggestions` populated according to the relaxation ladder and diagnostic `empty_pool_reason` for observability.

## Observability & SLO

- SLO: /compass/next p95 <= 60 ms @ 1k rps; p99 <= 120 ms. Degrade gracefully when ANN cold (return cached/stale curated).
- Logs (structured): query_id, limit_state, mode, ui_slots_req/resp, pool_size, top factors, curated_blocked_reason, empty_pool, emergency_used, served_from_cache, time_ms.
- Metrics: CTR per badge, route depth, explore share, diversity scores, empty pool %, cache hit %, ANN latency.
- Alerts: empty pool > 2%/hour, p95 > SLO, surge in abuse_locked, vector store growth > plan +20%.

## Testing & Readiness

### Acceptance

- [ ] /compass/next respects requested slots but may lower ui_slots; response echoes requested value and limit_state.
- [ ] Lite mode (limit_state=exceeded_lite) returns exactly 2 slots, curated priority, t=0.15, K=16, no random/echo.
- [ ] Near-limit reduces K by >=25%, disables explore, lowers epsilon to 0, and flips back to normal only after >30% quota remains.
- [ ] Curated candidates pass through EligibilityFilter; blocked ones report curated_blocked_reason.
- [ ] Anti-loop enforces 2-cycle block and 6-node window.
- [ ] DiversityGuard applies author/tag penalties and triggers orthogonal hops per mode thresholds.
- [ ] Selector softmax integrates curated boosts before scoring and respects deterministic seeding.
- [ ] Explanations available for every slot (badge + reason keys from the approved set).

### Test plan

- Unit tests: scoring normalisation per mode, diversity penalties, curated boost handling, softmax determinism via seeded randomness.
- Integration: session covering Normal -> Near-limit -> Lite transitions, verifying deterministic results with cache_seed and emergency reset behaviour.
- Simulation: graphs with loops, NSFW spikes, hard blocks; ensure relaxation ladder and fallback sequence fire correctly.
- A/B: near-limit thresholds (20% entry, 30% exit), Lite UI impact on CTR/route depth, emergency usage rate.
- Localisation: RU/EN tag taxonomies, explanation strings, badge dictionary, multi-locale NavigationPolicy.

## Resolved Details

- Badge set fixed to {trail, similar, trending, explore, limited, editorial}; localisation dictionary RU-EN maintained by content ops.
- `reason` payload is a JSON object of snake_case keys; allowed keys are {curated, tag_sim, echo, fresh, diversity_bonus, policy_penalty} with numeric values in [0,1] unless curated (0/1).
- Guest policy: identify as `anon_<hash(session_id)>`, quota 40 CompassQuery/day, near_limit at <=20% remaining, emergency unavailable, same slot rules as free tier.
- Diversity thresholds per mode: normal T=3, discover T=2 with mandatory orthogonal hop every 4 transitions, editorial T=4, near_limit T=3 (random off), lite T=4 (penalties only).
- Quota hysteresis reaffirmed: enter near_limit <=20%, exit >=30% (also encoded in Operational Controls).
- Determinism: cache_seed and selection use hash(user_id|session_id, origin_node_id, limit_state, mode) feeding the softmax sampler.

## Open Questions

- Canonical hash function for cache_seed (fnv1a, murmur, xxhash) and rollout plan across services.
- Operational ownership for emergency rate limiter and associated alerting thresholds.
- Benchmark targets for ANN latency after provider refactor and diversity guard tuning.



