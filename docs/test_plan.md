# Test Strategy and Plan

## 1. Current test landscape

Existing tests grouped by domain:

- **Authentication**: `tests/auth`, `tests/minimal_test.py`, `test_login_success`, `test_signup_success`, `tests/test_auth.py`.
- **Admin & RBAC**: Numerous `tests/test_admin_*`, `test_rbac.py` covering admin menus, metrics, cache, tags, etc.
- **Navigation & Search**: `test_navigation_cache.py`, `test_quest_search.py`, `test_node_search.py`.
- **Notifications & WebSockets**: `test_notifications`, `test_notification_ws.py`.
- **Quests & Achievements**: `test_event_quests.py`, `test_achievements.py`.
- **Payments**: `test_payments.py`.
- **Misc utilities**: `test_helpers.py`, `test_real_ip.py` etc.

Gaps identified:

- Navigation end‑to‑end flows (anonymous vs. authenticated).
- Moderation workflows and edge cases.
- WebSocket reconnection/error handling.
- Admin rights escalation and failure paths.
- Error handling for invalid data, 403/404 branches across modules.

## 2. Coverage baseline

Minimal suite run gives ~50% line coverage. High‑risk, low coverage modules include:

- `app/api/auth.py`, `app/api/admin.py`, `app/api/moderation.py` (<35%).
- Service layer: `app/services/navcache.py`, `app/services/notification_broadcast.py`, `app/services/quests.py` (<30%).

Target: **≥85% lines** and **≥70% branches**, with critical modules (`auth`, `navigation`, `notifications`, `admin`) enforced separately.

## 3. Planned tests

### Unit tests
- Cover branches for error codes, empty inputs, permission checks.
- Mock external services and database failures.

### Integration tests
- End‑to‑end signup/login/profile retrieval.
- Admin CRUD operations with permission matrix (success/403/404).
- Notification creation → delivery via WS.

### Contract tests
- Freeze response structures for public endpoints (JSON schema / snapshots).

### WebSocket tests
- Multiple clients subscribe, broadcast, reconnect with timeout.

### Regression suite
- 20 high‑priority flows marked with `@pytest.mark.regression` and collected via `pytest -m regression`.

## 4. Test data management

- Centralised fixtures using async SQLAlchemy session and `transactional` scope.
- Factory helpers to create users/roles/nodes; automatic teardown.
- Deterministic seed via `random.seed(0)` and time provider wrapper.

## 5. Lightweight load test

`scripts/light_load_test.py` asynchronously fires requests to selected endpoints. Metrics collected:

- total/failed requests
- mean and p95 latency
- per‑status counts

## 6. CI gates

- `ruff`, `black --check`, `mypy`.
- `pytest --cov=app tests` with coverage thresholds.
- Scheduled nightly run for integration/regression suites.

## 7. Documentation & DX

- README section on running tests, coverage, load test.
- Environment variable catalog (see `docs/env.md`).
- PR template guiding checklist.

