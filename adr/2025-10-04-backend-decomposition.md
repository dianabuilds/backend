# ADR 2025-10-04 — Правила распила backend на модульные компоненты

## Контекст

- Точка входа (`app/api_gateway/main.py`, `app/api_gateway/wires.py`) тянет все домены напрямую и содержит >35 импортов.
- Домены `platform.moderation` и `product.nodes` выросли в монолиты (по 2–3 тыс. строк на модуль), совмещая состояния, бизнес-логику и инфраструктуру.
- Нарушается слоистая модель `api > application > domain > adapters`: контроллеры выполняют SQL-запросы, application-слой напрямую работает с FastAPI/Redis.
- Импортные ограничения не контролируются, `importlinter` покрывает только два домена.

## Решение

1. **Слои и деревья доменов**
   - Для каждого домена обязательны подпакеты: `api`, `application`, `domain`, `adapters`, `docs`, `schema`. Дополнительные подпакеты (`commands`, `queries`, `services`, `tasks`) живут внутри `application`.
   - В крупных доменах (`platform.moderation`, `product.nodes`) обязательна декомпозиция до поддоменов второго уровня, где верхнеуровневые файлы лишь собирают публичные фасады.
   - `platform.moderation`: довести разнесение `application` на подпакеты `sanctions`, `tickets`, `content`, `appeals`, `ai_rules`, `users`, `overview`; HTTP-роуты перенести в `api/...` (по областям `content/http.py`, `appeals/http.py` и т. д.); в `adapters` разделить in-memory и SQL реализации, оставив зависимости только «application > adapters»; тесты сгруппировать по подпакетам и убрать обращения к старым путям.
   - `product.nodes`: выделить пакеты `api/admin`, `application/admin_queries`, `adapters/sql`, `adapters/memory`, `domain`; перенести вспомогательные утилиты (например, `_memory_utils`) в соответствующие подсекции `adapters`; разбить базовые модули так, чтобы размер не превышал 400 строк; переписать тесты на новую структуру импортов.
   - Дополнительно: product.* и platform.* домены теперь используют подкаталоги `adapters/sql` и `adapters/memory`; DI и контейнеры обновлены под новые пути.
   - Файлы уровней `application` и `api` не превышают 400 строк (DTO/типы допускаются до 800 строк с явным TODO на дальнейший распил).

2. **Единая схема DI/инициализации**
   - Реализовать dataclass-контейнеры в `app/api_gateway/container_registry.py`, описав зависимости и провайдеры доменов единообразно.
   - Заменить `register`, `provide_container` и прочие ручные функции на единый механизм регистрации и получения зависимостей.
   - Переписать `app/api_gateway/wires.py`, оставив лишь связывание контейнера и FastAPI-приложения; все домены переводятся на новый поток DI без временных подключений.
   - Главный контейнер (`apps.backend.Container`) остаётся поверхностным фасадом, подключающим плагины из реестра.

3. **Архитектурные ограничения и линтеры**
   - Пересобрать `importlinter.ini` с контрактами слоёв `api > application > domain > adapters > packages`.
   - Ввести правило запрета прямых импортов из `app.api_gateway` в `domains.*.(application|adapters)`.
   - Поддерживать waivers только для неизбежных исключений, фиксируя причины в ADR и сопровождающей документации.
   - Сделать проверки Import Linter частью CI; локальная цель `make imports-lint` не допускает пропуска проверки.

4. **Очистка и консолидация вспомогательных артефактов**
   - Пересмотреть snapshot'ы и тестовые фикстуры, заменив их фабриками или seed-пакетами перед распилом файлов.
   - Свести конфигурации (Makefile, служебные скрипты) к новой структуре директорий.
   - Обновлять `ARCHITECTURE.md`, README и ADR после завершения каждого этапа.
   - Удалять временные решения (старые `storage.py`, неиспользуемые DTO) сразу после миграции.

5. **Контроль качества и релиз**
   - После каждого блока запускать полный набор линтеров, mypy и тестов в CI.
   - Готовить промежуточные релизы с changelog, фиксируя завершённые шаги декомпозиции.
   - Перед распилом крупных модулей фиксировать поведение тестами (юнит/интеграционными) и прогонять пайплайн «до/после».
   - Поддерживать ADR (2025-10-04) в актуальном состоянии, отмечая статус, отступления и принятые решения.

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
- Тесты use-case слоёв (`domains/platform/moderation/tests`) расширены stub-репозиториями, чтобы фиксировать интеграцию use-case - presenter - repository без реальной БД.
- Домен platform.flags переведён на слой presenter/use_cases; HTTP теперь делегирует в `application.commands`/`application.queries`, сериализация вынесена в `application.presenter`, добавлены юнит-тесты `tests/unit/platform/flags/test_commands_queries.py`.
- У admin templates из platform.notifications выделены use-case и presenter, добавлены unit-тесты `tests/unit/platform/notifications/test_template_use_cases.py`.

- В `domains/product/profile` переведён на commands/queries и typed presenter; HTTP больше не зависит от `UseCaseResult`.

- В `notifications/admin broadcast` HTTP слой переключён на use-case/presenter, ошибки и сериализация унифицированы.

- Notifications messages переведены на presenter/use-case; HTTP слой избавлен от сериализации и user-resolve логика вынесена в use-case.

- Moderation content переведён на presenter/use-case: HTTP вызывает use-case, сериализация и сборка ответов вынесена, добавлены unit-тесты.
- Домен moderation.users переведён на пакет `application/users` (commands/queries/use_cases/presenter/repository); HTTP-эндпоинты делегируют в use-case слой, а service остаётся тонким фасадом.
- Вернули совместимость по импортам через прокси-модуль `domains.platform.moderation.dtos` и alias-хелперы в presenter’ах (content/appeals), чтобы снять ModuleNotFound без массового правки клиентов.
- Presenter `appeals` и `content` обновлён для возврата типизированных ответов с поддержкой attribute access и unit-тестов; добавлены `_AttrDict` и alias `build_appeals_list_response`.
- Добавлены юнит-тесты `tests/unit/platform/moderation/test_users_commands_queries.py` и пакетные маркеры `tests/unit/__init__.py`/`product/__init__.py` для устранения конфликтов имён при сборке pytest.
- Для product-доменов внедрены create_repo-фабрики с проверкой DSN и окружения (packages.core.sql_fallback.evaluate_sql_backend) и ручками для in-memory fallback.
- DI-контейнер и admin HTTP в product.tags используют фабрики, деля in-memory TagUsageStore и безопасно работая без Postgres.
- AI-регистрию добавлена create_registry(settings, dsn=...), которая логирует и переключает репозиторий на память при недоступной БД.

### 2025-10-05

- Добавлен общий контракт `layers_platform_domains` в `importlinter.ini`: фиксируем слои `tests > wires > api > application > adapters > domain` для `platform.{moderation,notifications,flags,users}` и описываем временные подпакеты как optional.
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

### Backlog после 2025-10-05

1. **platform.moderation**
   - Завершить разнесение `application` на подпакеты `sanctions`, `tickets`, `content`, `appeals`, `ai_rules`, `users`, `overview`.
   - Перенести HTTP-роуты в `api/...` по областям (`content/http.py`, `appeals/http.py` и т. д.).
   - В `adapters` выделить in-memory и SQL реализации; импорты привести к направлению `application -> adapters`.
   - Обновить тесты, сгруппировав их по подпакетам и устранив обращения к старой структуре.

2. **product.nodes**
   - Выделить пакеты `api/admin`, `application/admin_queries`, `adapters/sql`, `adapters/memory`, `domain`.
   - Перенести вспомогательные утилиты (например, `_memory_utils`) в соответствующие подпакеты `adapters`.
   - Сократить базовые модули до ?400 строк, разделив HTTP- и сервисные слои.
   - Перевести тесты на новую структуру импортов.

3. **Единая схема DI/инициализации**
   - Реализовать dataclass-контейнеры в `app/api_gateway/container_registry.py` и описать провайдеры зависимостей.
   - Заменить ручные `register`/`provide_container` на единый механизм и переписать `app/api_gateway/wires.py` под новый поток.
   - Обновить домены на работу через контейнер, убрав временные подключения.

4. **Архитектурные ограничения и линтеры**
   - Пересобрать `importlinter.ini` под слои `api > application > domain > adapters > packages`.
   - Ввести запрет на импорты из `app.api_gateway` в `domains.*.(application|adapters)`.
   - Настроить обязательный запуск Import Linter в CI с документированными waiver'ами.

5. **Очистка, документация и релизы**
   - Заменить snapshot'ы фабриками/seed-пакетами и выровнять Makefile/скрипты под новую структуру.
   - Обновить `ARCHITECTURE.md`, README и ADR по итогам этапов; удалить устаревшие `storage.py` и DTO.
   - После каждого блока прогонять линтеры, mypy и тесты; выпускать промежуточные релизы с changelog и обновлять ADR 2025-10-04.


