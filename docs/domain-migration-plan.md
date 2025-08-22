# План миграции кода в доменные слои

Цель: перевести функциональность из «плоских» сервисов (`app/services/*`) и технических слоёв к целевым доменным пакетам (`app/domains/<domain>/{domain,application,infrastructure,api}`) с явными контрактами (портами) и чёткой изоляцией.

Стек:
- Backend: FastAPI, SQLAlchemy, Alembic.
- Домены уже частично заведены: ai, auth, quests, moderation, notifications, payments, premium, media, achievements, navigation, tags, users, worlds, search, telemetry.
- Реестр доменных роутеров: `app/domains/registry.py`.

## Текущий этап (P1): доменные роутеры и зачистка «тонких прокси»
Что уже сделано в рамках P1
- Консолидация роутеров: доменный агрегатор AI — единственная точка подключения; убраны дубли в entrypoint/registry.
- Tags: перенос merge в домен (репозиторий/сервис), корректные подсчёты и защита от дублей алиасов; публичный список тегов вынесен в доменный роутер; legacy-прокси удалены.
- Nodes: публичные ручки сведены к доменным роутерам контента/навигации, файл переведён в чистый тонкий прокси.
- Quests: публичные ручки перенесены в доменный роутер, файл API заменён на тонкий прокси.
- AI Admin: тонкие прокси admin_ai_* удалены, используется доменный агрегатор; для validation/embedding задействованы доменные обёртки (временная мера).
- Модели: начата зачистка legacy-реэкспортов (tags, ai_settings, worlds, admin, achievements, notifications, payments).
- Точка входа: отключены дубли legacy-админ роутеров (navigation/restrictions/echo/audit/cache/menu/ratelimit/notifications/flags/search/metrics).

Что остаётся закрыть в P1 (конкретный чек-лист)
- AI
  - [ ] Завершить перенос: validation и embedding — из временных доменных обёрток в полноценные доменные routers/services/repositories.
  - [ ] После smoke — удалить соответствующие legacy-модули и обёртки.
- Тонкие прокси app/api
  - [x] nodes — переведён в тонкий прокси (доменные роутеры).
  - [x] tags — переведён в тонкий прокси (доменные роутеры).
  - [x] quests — переведён в тонкий прокси (доменные роутеры).
  - [ ] media — проверить покрытие доменными роутерами и удалить прокси.
  - [ ] navigation — проверить оставшиеся прокси и удалить после smoke.
  - [ ] traces — проверить и удалить после smoke.
  - [ ] transitions — проверить и удалить после smoke.
- Модели и импорты
  - [ ] Дочистить реэкспорты в app/models: user, node, feedback, transition, node_trace, echo_trace, moderation, moderation_case, quest, quest_version, event_quest, ai_generation/log, premium.
  - [ ] Прогнать codemod на замены импортов, проверить `scripts/check_no_legacy_imports.py` (зелёный).
- Контракты/OpenAPI/Frontend
  - [ ] Обновить OpenAPI под доменные роутеры (AI/Quests/Tags/Navigation) и синхронизировать admin-frontend (пути/типы).
  - [ ] Smoke: admin секции (AI jobs/logs/paging/cursor, rate limits, settings, stats; tags admin; navigation admin), публичные страницы (nodes/quests/tags).
- Миграции и качество
  - [ ] Alembic: прогон миграций «с нуля» и из текущего состояния (без конфликтов), индексы для горячих запросов (по плану P2 можно частично сделать уже сейчас).
  - [ ] pytest -q, e2e-smoke, базовые метрики/логи на доменных путях.

Критерии готовности P1 (Definition of Done)
- Все используемые фронтендом ручки подключены через доменные роутеры (прямых legacy-проксей нет).
- Legacy-реэкспорты моделей в app/models удалены; импорты только доменные/core.
- `scripts/check_no_legacy_imports.py` — зелёный, дублей роутов нет.
- OpenAPI соответствует фактическим доменным ручкам; admin-frontend работает на доменных путях.
- Миграции применяются чисто; тесты зелёные; базовый smoke пройден.

Доменные слои (целевой стиль папок на домен):
- domain: модели предметной области (Entity, Value Object, Policy), инварианты, доменные события.
- application: сценарии использования (use-cases), команды/запросы, порты (интерфейсы) к инфраструктуре.
- infrastructure: реализации портов (репозитории, клиенты, кеши, провайдеры), маппинги ORM, интеграции.
- api: контроллеры/роутеры FastAPI, схемы запросов/ответов, валидации и deps.

Ключевые принципы:
- Зависимости направлены внутрь: api -> application -> domain; infrastructure зависит от application/domain, но не наоборот.
- Порты в application; реализации портов в infrastructure.
- Доменные события (outbox/publish) — через application уровни; транспорт/логирование — в infrastructure.
- Бизнес-правила и инварианты — в domain; отсутствие побочных эффектов.
- Никакой прямой инфраструктуры в сценариях; только через порты.

Инвентаризация service-модулей и целевое размещение:
- ai:
  - app/services/ai_settings.py → app/domains/ai/application/settings_service.py (+ порты)
  - app/services/ai_pricing.py → app/domains/ai/application/pricing_service.py
  - app/services/ai_quests.py → app/domains/ai/application/integration/quests_bridge.py (координация с quests)
  - app/services/llm_circuit.py → app/domains/ai/application/circuit_service.py
  - app/services/llm_metrics.py → app/domains/telemetry/application/llm_metrics_facade.py (порт) + infrastructure/llm_metrics_adapter.py
  - app/services/llm_providers/* → app/domains/ai/infrastructure/providers/*
- payments:
  - app/services/payments.py → app/domains/payments/application/payments_service.py
  - app/services/payments_manager.py → app/domains/payments/application/manager.py
  - app/services/payments_ledger.py → app/domains/payments/infrastructure/repositories/ledger_repository.py
  - app/services/nft.py → (открытый вопрос) payments/application/nft_service.py или media/application/nft_service.py — уточнить требования
- premium:
  - app/services/plans.py → app/domains/premium/application/plan_service.py
  - app/services/quotas.py → app/domains/premium/application/quota_service.py
  - app/services/user_quota.py → app/domains/premium/application/user_quota_service.py
- quests:
  - app/services/quests.py → app/domains/quests/application/quest_service.py (согласовать с имеющимися: gameplay/authoring/versions)
  - app/services/quests_editor.py → app/domains/quests/application/editor_service.py
- notifications:
  - app/services/notifications.py → app/domains/notifications/application/notify_service.py
  - app/services/notification_ws.py → app/domains/notifications/infrastructure/transports/websocket.py
  - app/services/notification_broadcast.py → app/domains/notifications/infrastructure/broadcast.py
  - app/services/mail.py → app/domains/notifications/infrastructure/mail.py (порт IMailGateway в application)
- media:
  - app/services/blob_store.py → app/domains/media/infrastructure/storage/blob_store.py
  - app/services/storage.py → app/domains/media/application/storage_service.py (порт IStorageGateway)
- navigation:
  - app/services/navcache.py → app/domains/navigation/infrastructure/cache.py (+ application facade)
- search:
  - app/services/search_config.py → app/domains/search/application/config_service.py
- telemetry:
  - app/services/audit.py → app/domains/telemetry/application/audit_service.py
  - app/services/generation_logs.py → app/domains/telemetry/application/generation_log_service.py
  - app/services/worker_metrics.py → app/domains/telemetry/application/worker_metrics_service.py
  - app/services/raw_payloads.py → app/domains/telemetry/infrastructure/raw_payload_store.py (+ application порт)
- tags:
  - app/services/tags.py → app/domains/tags/application/tag_service.py
  - app/services/tags_admin.py → app/domains/tags/application/tag_admin_service.py + api/routers.py
- admin:
  - app/services/admin_menu.py → app/domains/admin/application/menu_service.py
- core/tech (сквозные):
  - app/services/feature_flags.py → app/core/feature_flags.py (порт IFeatureFlags в application доменов, реализация тут)
  - app/services/cache.py → app/core/cache.py (низкоуровневый адаптер — вызывать из infrastructure доменов)
  - app/services/outbox.py → app/core/outbox.py (общий механизм публикации событий)
  - app/services/queries.py → app/core/db/query.py (если нужно) или распилить по доменным репозиториям
  - Примечание: «core» — технический слой, не домен.

Порядок миграции (итерациями — безопасные шаги):
1) Базовые тех.сквозняки
   - Выделить core/outbox.py, core/feature_flags.py, core/cache.py, core/db/query.py (минимум интерфейсы).
   - Обновить импорты в минимально затронутых местах (или создать адаптеры-«прослойки»).
2) Telemetry (низкий риск)
   - Перенести audit, generation_logs, worker_metrics, llm_metrics (порт + адаптер).
   - Включить новую реализацию через application фасады; оставить старые точки входа как thin proxy (до полной выпилки).
3) Tags
   - Перенос tag_service и admin-функций. Добавить `app/domains/tags/api/routers.py` (и подключение уже есть в registry).
4) Media
   - Выделить IStorageGateway и перенос blob_store, storage.
5) Notifications
   - Перенос notify_service, mail, ws, broadcast. Разделить application (порты) и infrastructure (SMTP, WS, pub-sub).
6) Payments
   - Перенос основной логики payments, manager и ledger repo. Выделить доменные сущности транзакций.
7) AI
   - Перенос настроек/прайсинга/провайдеров/цепочек. Границы с telemetry (метрики) и quests (ai_quests) оформить портами.
8) Quests
   - Согласовать с существующими файлами домена (gameplay/authoring/versions). Перенести quests_service, editor.
9) Navigation, Search, Premium
   - Навигационный кеш, поисковые конфиги, планы/квоты — по аналогии.

Definition of Done для переноса файла/функционала:
- Определены доменные сущности и инварианты (domain/*).
- Use-case описан в application/* и не зависит от инфраструктуры.
- Порты объявлены в application/ports/* и закрывают внешние зависимости.
- Реализации портов живут в infrastructure/*; скрывают детали БД/кэша/HTTP/SMTP/WS.
- API-роутер использует только application слой.
- Регистрация роутера добавлена/проверена в `app/domains/registry.py`.
- Тесты: unit на domain/application, интеграционные на infrastructure, смоук е2е ручки.
- Старые импорты либо удалены, либо оставлены как thin proxy с TODO и предупреждением (на переходный период ≤2 итераций).

Тактика «thin proxy» (для безопасного рефакторинга):
- В старом `app/services/<name>.py` оставить функции обёртки, вызывающие новый application use-case. Пометить Deprecated.
- Логирование при использовании устаревших точек.
- Постепенно перевести все вызовы и удалить файл.

Риски и смягчение:
- Сквозные зависимости между доменами → через порты (никаких прямых импортов infrastructure).
- Миграция БД/репозиториев → SRP: на каждый репозиторий — тест на контракты.
- Производительность при разделении → кеш-слой держать в infrastructure с прозрачными адаптерами.
- WS/SMTP/pubsub → чёткие границы транспортов; backpressure/ошибки — через telemetry.

Метрики прогресса:
- % модулей в app/services, у которых есть доменный аналог и thin proxy.
- % ручек API, которые уже используют application слой доменов.
- Кол-во циклических зависимостей (должно быть 0).

Дорожная карта (квартильная):
- Итер.1: core + telemetry + tags
- Итер.2: media + notifications
- Итер.3: payments + ai (часть)
- Итер.4: ai (оставшееся) + quests + premium + navigation + search
- В конце каждого этапа — чистка thin proxy.

Открытые вопросы:
- nft.py — принадлежность к payments или media: зависит от бизнес-владения. Требуется ревью требований.
- queries.py — сохранить как общий helper (core/db/query.py) или провести депривацию в пользу репозиториев.
- outbox/event-bus — единый механизм или по доменам; предложено: единый в core.

Примечания:
- Регистрация доменных роутеров уже предусмотрена в `app/domains/registry.py` — по мере переноса API добавлять `api/routers.py`.
- Названия портов: I<Capability>Port, реализации: <system>Adapter.
