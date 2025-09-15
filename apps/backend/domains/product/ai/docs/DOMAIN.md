# AI (Product) — Domain

Scope
- Provide a clean, minimal API for AI text generation decoupled from monolith internals.
- Record domain events and LLM metrics for observability.

API
- GET /v1/ai/health → {status}
- POST /v1/ai/generate {prompt} → {result}

Architecture
- Ports: Provider (async generate(prompt)->str)
- Service: wraps provider, emits events (ai.generation.started/completed), records LLM metrics.
- Adapters: wraps monolith IAIProvider to Provider port; outbox adapter writes to SQL `outbox` table.

Events
- ai.generation.started.v1 {prompt_len, provider, model}
- ai.generation.completed.v1 {latency_ms, result_len, provider, model}

Metrics (LLM)
- Counters: calls, errors
- Gauges: average latency
- Optionally tokens/cost when provider supplies them

Feature Flag
- FF_AI_V1_ENABLED toggles wiring and routes in the app.

Cutover
1) Enable flag in staging; verify generate + events + metrics.
2) Route client calls to /v1/ai/generate; monitor errors/latency.
3) Extend provider adapter for tokens/cost when ready; add presets/models if needed.

Security
- Minimal endpoints are public by default; add JWT/CSRF guards if required by product.

