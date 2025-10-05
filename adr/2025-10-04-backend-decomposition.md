# ADR 2025-10-04 — Правила распила backend на модульные компоненты

## Контекст

- Точка входа (`app/api_gateway/main.py`, `app/api_gateway/wires.py`) тянет все домены напрямую и содержит >35 импортов.
- Домены `platform.moderation` и `product.nodes` выросли в монолиты (по 2–3 тыс. строк на модуль), совмещая состояния, бизнес-логику и инфраструктуру.
- Нарушается слоистая модель `api → application → domain → adapters`: контроллеры выполняют SQL-запросы, application-слой напрямую работает с FastAPI/Redis.
- Импортные ограничения не контролируются, `importlinter` покрывает только два домена.

## Решение

1. **Слои и деревья доменов**
   - Для каждого домена обязательно наличие подпакетов: `api`, `application`, `domain`, `adapters`, `docs`, `schema`. Дополнительные подпакеты (`commands`, `queries`, `services`, `tasks`) создаются внутри `application`.
   - Внутри крупных доменов (например, `platform.moderation`, `product.nodes`) вводим поддомены второго уровня: `application/sanctions`, `application/tickets`, `api/admin`, `adapters/sql`, `adapters/redis` и т.п. Файл верхнего уровня только собирает публичные фасады.
   - Файл уровня `application` или `api` не должен превышать 400 строк. Исключения допустимы только для DTO/типов (до 800 строк) при явном указании в докстринге и TODO на распил.

2. **DI/контейнеры**
   - Каждый домен экспортирует функцию `register(container_registry)` или `provide_container()`, которая возвращает dataclass контейнера и его зависимости. Точка входа регистрирует домены через общий реестр (`app/api_gateway/container_registry.py`).
   - Главный контейнер (`apps.backend.Container`) ничего не знает о внутренних модулях доменов; он загружает плагины по списку, описанному в конфигурации.
   - Любые прямые импорты доменов внутри `app/api_gateway/wires.py` запрещены: только обращение к реестру.

3. **Контракты импорта**
   - Расширяем `importlinter.ini`: для каждого домена вводим контракт `layers` (api → application → domain → adapters) и запрещаем кросс-доменные импорты вне публичных клиентов.
   - Добавляем контракт `forbidden` для `app.api_gateway` против прямых импортов из `domains.*.*.(application|adapters)`.

4. **Рабочий процесс**
   - Перед распилом крупного файла — snapshot-фиксация поведения (юнит/интеграционные тесты или контракты).
   - Рефакторинг выполняется итеративно: сначала перенос логики в подпакеты, затем вынос общих сценариев в отдельные bounded contexts.
   - Любое отклонение от правил оформляется через ADR и временный `WAIVER` в `importlinter.ini`.

## Последствия

- Контейнеры становятся взаимозаменяемыми; легко выделять домены в отдельные сервисы.
- Поддерживается читаемость и тестируемость: крупные файлы распиливаются, контроллеры становятся тонкими.
- Появляется механизм контроля архитектурных границ на CI.
- Начальные усилия потребуют миграции существующих доменов по новым правилам и обновления документации.
## Реализация (2025-10-04)

- В `apps/backend/domains/platform/moderation/application` добавлены модули `sanctions.py`, `reports.py`, `tickets.py`, `appeals.py`, `ai_rules.py`; основной `service.py` теперь лишь связывает их через декораторы `_ensure_loaded_decorator`/`_mutating_operation`.
- DTO и in-memory записи вынесены в `domain/records.py`, операции с пользователями — в `application/users.py`.
- Админские API нод (`admin_nodes.py`, `admin_analytics.py`, `admin_bans.py`, `admin_comments.py`, `admin_moderation.py`) переводены на `AdminQueryError` и тонкие обёртки поверх `application/admin_queries.py`.
- `importlinter` и `compileall` выполняются для новых модулей в рамках локальной проверки.
- Методы преобразования контента и пользователей вынесены в `application/content.py` и `application/users.py`; `service.py` теперь только агрегирует зависимости.
- Добавлены юнит-тесты для модулей `content`, `overview`, `sanctions`, `reports`, `tickets`, `appeals`, `ai_rules` (`apps/backend/domains/platform/moderation/tests`).
- `importlinter.ini` расширен контрактами для `platform.flags`, `platform.search`, `platform.telemetry` и ограничениями на кросс-доменные импорты слоя `application`.
- Фикстура `tests/conftest.py` служит шаблоном подготовки данных для модульного распила других доменов.
- Фабрики сущностей модерации вынесены в `application/factories.py`; `service.py` и тестовые фикстуры используют их вместо приватных методов.
- Общие утилиты (ISO-формат, парс даты, пагинация, генерация id) собраны в `application/common.py`; сервис и подмодули используют их вместо приватных методов.
- Application-слой разбит на use-case пакеты (`content`, `reports`, `tickets`, `appeals`, `ai_rules`) с `queries.py`/`commands.py`; `service.py` теперь только биндинги.
- API-эндпоинты (`content`, `reports`, `tickets`, `appeals`, `ai_rules`) вызывают новые use-case функции вместо прямого доступа к сервису, сохраняя единый слой приложения.
- Добавлен репозиторий `application/content/repository.py` с методами `list_queue`, `load_content_details`, `record_decision`; use-case (`queries.py`/`commands.py`) и API обращаются к нему вместо прямой работы с `Engine`.
- Репозиторий покрыт модульными тестами (`tests/test_content_repository.py`) с асинхронными фейк-движками, что фиксирует поведение фильтров и истории решений.
- Команды контента возвращают полный ответ (`moderation_status`, `db_state`), поэтому HTTP-слой перестал пост-обрабатывать решения; добавлены юнит-тесты `test_content_commands.py`.
- Добавлены presenter-хелперы (`application/content/presenter.py`) и тесты на команды, чтобы формирование ответов происходило на уровне use-case, а HTTP возвращал данные без пост-обработки.
- Добавлены presenter-хелперы (`application/presenters/enricher.py`) и отдельные presenter-модули для `reports`, `tickets`, `appeals`, `ai_rules`; они объединяют DTO с SQL-снимками.
- HTTP-эндпоинты `reports`, `tickets`, `appeals` создают `repository` через `create_repository(settings)` и делегируют всю бизнес-обработку в use-case/ presenter слой.
- Реализованы SQL-репозитории для `reports`, `tickets`, `appeals` с in-memory fallback и модульными тестами (`tests/unit/platform/moderation/test_*_repository.py`), покрывающими выборку и обновление.
- CI пайплайн (`ci.yml`) запускает `pytest` с `pytest-cov` и порогом `--cov-fail-under=80` для SQL-репозиториев модерации, чтобы блокировать регрессы покрытия.

- Добавлены юнит-тесты `tests/unit/platform/moderation/test_presenters.py`, проверяющие фабрику enricher и доменные presenter’ы на merge metadata/history.
- Тесты use-case слоёв (`domains/platform/moderation/tests`) расширены stub-репозиториями, чтобы фиксировать интеграцию use-case ↔ presenter ↔ repository без реальной БД.
- Домен platform.flags переведён на слой presenter/use_cases; HTTP теперь делегирует в `application.use_cases`, сериализация вынесена в `application.presenter`, добавлены юнит-тесты `tests/unit/platform/flags/test_use_cases.py`.
- У admin templates из platform.notifications выделены use-case и presenter, добавлены unit-тесты `tests/unit/platform/notifications/test_template_use_cases.py`.

- В `domains/product/profile` выделены presenter/use-case модули; сервис возвращает `ProfileView`, HTTP-слой и настройки используют единый `UseCaseResult` с ETag/ошибками.

- В `notifications/admin broadcast` HTTP слой переключён на use-case/presenter, ошибки и сериализация унифицированы.

- Notifications messages переведены на presenter/use-case; HTTP слой избавлен от сериализации и user-resolve логика вынесена в use-case.

- Moderation content переведён на presenter/use-case: HTTP вызывает use-case, сериализация и сборка ответов вынесена, добавлены unit-тесты.
- Домен moderation.users переведён на пакет `application/users` (commands/queries/use_cases/presenter/repository); HTTP-эндпоинты делегируют в use-case слой, а service остаётся тонким фасадом.
- Вернули совместимость по импортам через прокси-модуль `domains.platform.moderation.dtos` и alias-хелперы в presenter’ах (content/appeals), чтобы снять ModuleNotFound без массового правки клиентов.
- Presenter `appeals` и `content` обновлён для возврата типизированных ответов с поддержкой attribute access и unit-тестов; добавлены `_AttrDict` и alias `build_appeals_list_response`.
- Добавлены юнит-тесты `tests/unit/platform/moderation/test_users_use_cases.py` и пакетные маркеры `tests/unit/__init__.py`/`product/__init__.py` для устранения конфликтов имён при сборке pytest.
- Для product-доменов внедрены create_repo-фабрики с проверкой DSN и окружения (packages.core.sql_fallback.evaluate_sql_backend) и ручками для in-memory fallback.
- DI-контейнер и admin HTTP в product.tags используют фабрики, деля in-memory TagUsageStore и безопасно работая без Postgres.
- AI-регистрию добавлена create_registry(settings, dsn=...), которая логирует и переключает репозиторий на память при недоступной БД.

### 2025-10-05

- Добавлен общий контракт `layers_platform_domains` в `importlinter.ini`: фиксируем слои `tests → wires → api → application → adapters → domain` для `platform.{moderation,notifications,flags,users}` и описываем временные подпакеты как optional.
- В конфиге зафиксирован waiver на `notifications.workers.broadcast -> notifications.wires` (рабочая обходная схема до перевода worker-ботстрапа в реестр контейнеров).
- CI и локальный `make imports-lint` выполняют `python -m importlinter.cli lint --config importlinter.ini`, что делает архитектурные проверки обязательными перед мёрджем.
- Контейнерный слой обновлён: `app/api_gateway/container_registry.py` регистрирует доменные фабрики, `platform.notifications` использует подпакет `application/delivery` с `NotificationEvent` и `DeliveryService`, а `app/api_gateway/wires.py` берёт репозитории/сервисы через реестр.
- Добавлен пакет `packages.core.testing` с функциями `is_test_mode`, `override_test_mode` и единым переключателем "боевой"/"in-memory" инфраструктуры.
- Контейнеры notifications/moderation/nodes используют фабрики `select_backend(test_mode=…)`; для уведомлений реализованы полноценные in-memory адаптеры (репозитории, матрица, аудит, broadcast/audience resolver).
- Audit в тестовом режиме переключается на ``InMemoryAuditRepo``, что убирает специальные условные ветки из `_emit_admin_activity`.
- Для административных API нод добавлен общий helper `resolve_memory_node`, устранив копипасту по модулям.
- Интеграционный тест `tests/integration/test_app_startup.py` гарантирует запуск `TestClient(app)` без внешних сервисов; разработчикам рекомендуется использовать `scripts/run-tests.ps1` для локального прогона.
#### Ограничения тестового режима

- События работают на `InMemoryOutbox`/`InMemoryEventBus`: обработчики вызываются синхронно, данных в Redis нет.
- Уведомления используют in-memory репозитории и аудит; email/webhook-каналы только логируют payload.
- Аудит пишет события в `InMemoryAuditRepo`, поэтому история теряется после завершения процесса.
- Контейнер модерации не сохраняет снимок в Postgres, состояние хранится в памяти.
- Репозитории product-доменов переключаются на seeded in-memory адаптеры, данные сбрасываются между запусками.
- Поиск работает на `InMemoryIndex` и in-memory cache, `search_persist_path` и Redis игнорируются.
