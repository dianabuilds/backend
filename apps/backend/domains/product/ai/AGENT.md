# AI (Product) — AGENT Guide

Purpose
- Provide a clean DDD API for AI text generation atop existing providers.
- Emit domain events and LLM metrics for observability and analytics.

Scope
- Minimal endpoints (Phase 1/2):
  - `GET /v1/ai/health` → `{status}`
  - `POST /v1/ai/generate` → `{result}` (body: `{prompt}`)
- Internals:
  - Service uses a Provider port (async `generate(prompt) -> str`).
  - Adapter wraps the monolith `IAIProvider` into the DDD port.
  - Events and LLM metrics are recorded around calls.

Storage
- No schema changes in Phase 1/2. Events go to SQL outbox, metrics live in the platform telemetry sink.

Feature Flag
- `FF_AI_V1_ENABLED` (bool, default True) toggles wiring and routes.

Wiring
- Adapter: `apps/backend/app/bridges/ai_provider_adapter.py` → wraps `app.providers.ai.IAIProvider`.
- Integrator: `apps/backend/app/bridges/ai_integration.py`
  - Resolves `IAIProvider` from DI (punq), creates `AIService` with `SAOutboxAdapter`, exposes at `app.state.container.ai_service`.
- App inclusion: `apps/backend/app/main.py` — calls `wire_ai_service` + `include_ai_router` under the feature flag.

Events (outbox)
- `ai.generation.started.v1` `{prompt_len, provider, model}`
- `ai.generation.completed.v1` `{latency_ms, result_len, provider, model}`
- Outbox adapter: `apps/backend/app/bridges/outbox_adapter.py` (writes to `outbox` table).

Metrics (LLM)
- Facade: `apps/backendDDD/domains/platform/telemetry/application/metrics_registry.py: llm_metrics`.
- Labels: `{provider, model, stage}`; current stage=`unknown` (can be specialized later).
- Recorded: calls/errors counters, latency, optional tokens/cost if the provider exposes them.

Contracts
- Provider port: `apps/backendDDD/domains/product/ai/application/ports.py` → `Provider.generate(prompt) -> str`.
- Service: `apps/backendDDD/domains/product/ai/application/service.py` — emits events + metrics.
- API: `apps/backendDDD/domains/product/ai/api/http.py` — thin wrapper, validates `prompt`.

Auth/Security
- The minimal routes do not enforce auth by default. If required, add JWT guard and CSRF as in other product domains.

Testing
- Dev/Test providers come from `register_providers` mapping; expect `fake:` prefixes.
- Smoke:
  - `POST /v1/ai/generate {"prompt":"hi"}` → `{"result":"fake:hi"}`
  - Outbox contains started/completed events.
  - LLM metrics updated (see telemetry metrics exposition if wired to Prometheus).

Next Steps
- Extend Provider to return token/cost for richer metrics.
- Add presets/models routes if needed (keep them decoupled from monolith settings).
- Add idempotency and request tracing if client retries are expected.

