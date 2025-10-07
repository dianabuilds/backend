# ADR 2025-10-04    backend   

## 

-   (`apps/backend/app/api_gateway/main.py`, `apps/backend/app/api_gateway/wires.py`)       >35 .
-  `platform.moderation`  `product.nodes`    ( 23 .   ),  , -  .
-    `api > application > domain > adapters`:   SQL-, application-    FastAPI/Redis.
-    , `importlinter`    .

## 

1. **   **
   -     : `api`, `application`, `domain`, `adapters`, `docs`, `schema`.   (`commands`, `queries`, `services`, `tasks`)   `application`.
   -    (`platform.moderation`, `product.nodes`)      ,       .
   - `platform.moderation`:   `application`   `sanctions`, `tickets`, `content`, `appeals`, `ai_rules`, `users`, `overview`; HTTP-   `api/...` (  `content/http.py`, `appeals/http.py`  . .);  `adapters`  in-memory  SQL ,    application > adapters;          .
   - `product.nodes`:   `api/admin`, `application/admin_queries`, `adapters/sql`, `adapters/memory`, `domain`;    (, `_memory_utils`)    `adapters`;    ,     400 ;      .
   - : product.*  platform.*     `adapters/sql`  `adapters/memory`; DI      .
   -   `application`  `api`   400  (DTO/   800    TODO   ).

2. **  DI/**
   -  dataclass-  `apps/backend/app/api_gateway/container_registry.py`,      .
   -  `register`, `provide_container`           .
   -  `apps/backend/app/api_gateway/wires.py`,      FastAPI-;       DI   .
   -   (`apps.backend.Container`)   ,    .

3. **   **
   -  `importlinter.ini`    `api > application > domain > adapters > packages`.
   -       `apps.backend.app.api_gateway`  `domains.*.(application|adapters)`.
   -  waivers    ,    ADR   .
   -   Import Linter  CI;   `make imports-lint`    .

4. **    **
   -  snapshot'   ,     seed-   .
   -   (Makefile,  )    .
   -  `ARCHITECTURE.md`, README  ADR    .
   -    ( `storage.py`,  DTO)   .

5. **   **
   -       , mypy    CI.
   -     changelog,    .
   -        (/)    /.
   -  ADR (2025-10-04)   ,  ,    .

## 

-   ;      .
-    :   ,   .
-       CI.
-            .
##  (2025-10-04)

-  `apps/backend/domains/platform/moderation/application`   `sanctions.py`, `reports.py`, `tickets.py`, `appeals.py`, `ai_rules.py`;  `service.py`       `_ensure_loaded_decorator`/`_mutating_operation`.
- DTO  in-memory    `domain/records.py`,      `application/users.py`.
-  API  (`admin_nodes.py`, `admin_analytics.py`, `admin_bans.py`, `admin_comments.py`, `admin_moderation.py`)   `AdminQueryError`     `application/admin_queries.py`.
- `importlinter`  `compileall`        .
-        `application/content.py`  `application/users.py`; `service.py`    .
-  -   `content`, `overview`, `sanctions`, `reports`, `tickets`, `appeals`, `ai_rules` (`apps/backend/domains/platform/moderation/tests`).
- `importlinter.ini`    `platform.flags`, `platform.search`, `platform.telemetry`    -   `application`.
-  `tests/conftest.py`         .
-      `application/factories.py`; `service.py`        .
-   (ISO-,  , ,  id)   `application/common.py`;        .
- Application-   use-case  (`content`, `reports`, `tickets`, `appeals`, `ai_rules`)  `queries.py`/`commands.py`; `service.py`   .
- API- (`content`, `reports`, `tickets`, `appeals`, `ai_rules`)   use-case      ,    .
-   `application/content/repository.py`   `list_queue`, `load_content_details`, `record_decision`; use-case (`queries.py`/`commands.py`)  API        `Engine`.
-     (`tests/test_content_repository.py`)   -,       .
-      (`moderation_status`, `db_state`),  HTTP-  - ;  - `test_content_commands.py`.
-  presenter- (`application/content/presenter.py`)    ,       use-case,  HTTP    -.
-  presenter- (`application/presenters/enricher.py`)   presenter-  `reports`, `tickets`, `appeals`, `ai_rules`;   DTO  SQL-.
- HTTP- `reports`, `tickets`, `appeals`  `repository`  `create_repository(settings)`    -  use-case/ presenter .
-  SQL-  `reports`, `tickets`, `appeals`  in-memory fallback    (`tests/unit/platform/moderation/test_*_repository.py`),    .
- CI  (`ci.yml`)  `pytest`  `pytest-cov`   `--cov-fail-under=80`  SQL- ,    .

-  - `tests/unit/platform/moderation/test_presenters.py`,   enricher   presenter  merge metadata/history.
-  use-case  (`domains/platform/moderation/tests`)  stub-,    use-case - presenter - repository   .
-  platform.flags    presenter/use_cases; HTTP    `application.commands`/`application.queries`,    `application.presenter`,  - `tests/unit/platform/flags/test_commands_queries.py`.
-  admin templates  platform.notifications  use-case  presenter,  unit- `tests/unit/platform/notifications/test_template_use_cases.py`.

-  `domains/product/profile`   commands/queries  typed presenter; HTTP     `UseCaseResult`.

-  `notifications/admin broadcast` HTTP    use-case/presenter,    .

- Notifications messages   presenter/use-case; HTTP      user-resolve    use-case.

- Moderation content   presenter/use-case: HTTP  use-case,     ,  unit-.
-  moderation.users    `application/users` (commands/queries/use_cases/presenter/repository); HTTP-   use-case ,  service   .
-      - `domains.platform.moderation.dtos`  alias-  presenter (content/appeals),   ModuleNotFound    .
- Presenter `appeals`  `content`        attribute access  unit-;  `_AttrDict`  alias `build_appeals_list_response`.
-  - `tests/unit/platform/moderation/test_users_commands_queries.py`    `tests/unit/__init__.py`/`product/__init__.py`       pytest.
-  product-  create_repo-   DSN   (packages.core.sql_fallback.evaluate_sql_backend)    in-memory fallback.
- DI-  admin HTTP  product.tags  ,  in-memory TagUsageStore     Postgres.
- AI-  create_registry(settings, dsn=...),          .

### 2025-10-05

-    `layers_platform_domains`  `importlinter.ini`:   `tests > wires > api > application > adapters > domain`  `platform.{moderation,notifications,flags,users}`      optional.
-    waiver  `notifications.workers.broadcast -> notifications.wires` (     worker-   ).
- CI   `make imports-lint`  `python -m importlinter.cli lint --config importlinter.ini`,       .
-   : `apps/backend/app/api_gateway/container_registry.py`   , `platform.notifications`   `application/delivery`  `NotificationEvent`  `DeliveryService`,  `apps/backend/app/api_gateway/wires.py`  /  .
-   `packages.core.testing`   `is_test_mode`, `override_test_mode`    ""/"in-memory" .
-  notifications/moderation/nodes   `select_backend(test_mode=)`;     in-memory  (, , , broadcast/audience resolver).
- Audit      ``InMemoryAuditRepo``,       `_emit_admin_activity`.
-   API    helper `resolve_memory_node`,    .
-   `tests/integration/test_app_startup.py`   `TestClient(app)`   ;    `scripts/run-tests.ps1`   .
####   

-    `InMemoryOutbox`/`InMemoryEventBus`:   ,   Redis .
-   in-memory   ; email/webhook-   payload.
-     `InMemoryAuditRepo`,      .
-       Postgres,    .
-  product-   seeded in-memory ,    .
-    `InMemoryIndex`  in-memory cache, `search_persist_path`  Redis .

### Backlog  2025-10-05

1. **platform.moderation**
   -   `application`   `sanctions`, `tickets`, `content`, `appeals`, `ai_rules`, `users`, `overview`.
   -  HTTP-  `api/...`   (`content/http.py`, `appeals/http.py`  . .).
   -  `adapters`  in-memory  SQL ;     `application -> adapters`.
   -  ,          .

2. **product.nodes**
   -   `api/admin`, `application/admin_queries`, `adapters/sql`, `adapters/memory`, `domain`.
   -    (, `_memory_utils`)    `adapters`.
   -     ?400 ,  HTTP-   .
   -      .

3. **  DI/**
   -  dataclass-  `apps/backend/app/api_gateway/container_registry.py`    .
   -   `register`/`provide_container`      `apps/backend/app/api_gateway/wires.py`   .
   -      ,   .

4. **   **
   -  `importlinter.ini`   `api > application > domain > adapters > packages`.
   -      `apps.backend.app.api_gateway`  `domains.*.(application|adapters)`.
   -    Import Linter  CI   waiver'.

5. **,   **
   -  snapshot' /seed-   Makefile/   .
   -  `ARCHITECTURE.md`, README  ADR   ;   `storage.py`  DTO.
   -     , mypy  ;     changelog   ADR 2025-10-04.

##   2025-10-07

- Nodes API   : HTTP- `domains/product/nodes/api/http.py`   `public/` , -   `application/use_cases/**`, SQL-   `infrastructure/*`.  unit- `tests/unit/nodes/test_use_cases.py`.
- Navigation API     : `navigation/api/http.py`  `public`/`admin` , use-case  (`transition.py`, `relations_admin.py`)   FastAPI,    `infrastructure/engine.py`  `relations.py`. Unit-   `tests/unit/navigation`.
-  (`apps/backend/ARCHITECTURE.md`) ,      .
- Billing:  use-case    `BillingUseCases`    `BillingSettingsUseCase`, SQL-   `infrastructure/sql`,     .  unit-/smoke- (`tests/unit/billing`, `tests/smoke/test_api_billing.py`).

