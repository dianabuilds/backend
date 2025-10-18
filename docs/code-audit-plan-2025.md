# План аудита кодовой базы (октябрь 2025)

## Цель и охват
- Провести сквозной аудит фронтенда (`apps/web`), бэкенда (`apps/backend`), инфраструктуры и процессов.
- Выявить дубли, мертвый код, нарушения архитектурных границ, проблемы безопасности и производительности.
- Подготовить очередь задач и ADR-решения, не нарушая текущую стабильность.

## Исходные артефакты и наблюдения
- `README.md`, `apps/backend/ARCHITECTURE.md`, `apps/web/README.md` — базовая карта сервисов, слойность и правила работы с шаблоном.
- `apps/web/frontend-audit.md` — перечень дублей, устаревших компонентов и UX-проблем.
- Логи CI: `typecheck.log`, `mypy.log`, `coverage.xml` — фиксация текущих ошибок типов и покрытия (82.83% по moderation repos).
- CI/CD: `.github/workflows/ci.yml`, `ci-nightly.yml`, `docs.yml` — автоматизация линтов, типизации, генерации схем.
- Конфигурации качества: `pyproject.toml`, `eslint.config.js`, `vitest.config.ts`, `cypress.config.ts`, `qodana.yaml`.
- Документы SEO/перф: `apps/web/homepage-seo-guidelines.md`, ADR `adr/2025-10-09-homepage-configuration-tasks.md` (раздел P5).

## Критерии качества и метрики
- **Фронтенд**: ESLint/Vitest без ошибок, Lighthouse score ≥ 85 (мобайл), bundle size контроль, SSR/LCP ≤ 2.5s на стенде.
- **Бэкенд**: mypy strict = 0 ошибок, ruff clean, pytest (unit+integration) ≥ 85% покрытия по ключевым доменам, import-linter без нарушений.
- **Инфраструктура**: CI проходит ≤ 10 минут на PR, nightly slow-тесты стабильны, документация (OpenAPI) обновляется на каждый merge.
- **Безопасность**: секреты только в .env (с валидацией `pydantic-settings`), bandit/vulture/pip-audit подключены через `scripts/validate_repo` (нужно восстановить).

## Волны аудита
### Волна 0 — Подготовка
- Актуализировать карту модулей и зависимостей (madge/`eslint-plugin-boundaries` для фронта, `importlinter` снапшот для бэка).
- Восстановить/дописать `scripts/validate_repo.py` или обновить документацию `CodeValidator.md`.
- Собрать базовые метрики: Lighthouse отчеты, pytest coverage, время ответов API (httpx/builtin бенчмарки), размер бандла `@caves/web`.
- Согласовать перечень целевых показателей и приемочных критериев с продуктом/безопасностью.

### Базовые метрики (октябрь 2025)
- Lighthouse performance (мобайл): home 0.61, dev-blog 0.73 (`var/lighthouse-home.json`, `var/lighthouse-devblog.json`).
- Lighthouse SEO: home 0.92 (цель 0.95) — требуется корректировка мета-тегов.
- Entry bundle (JS): 1.84 MB (`var/frontend-bundle.json`).
- pytest coverage: 82.83% общий показатель (`coverage.xml`, `var/coverage-summary.json`).
- Bandit: падение на B110/B105/B311 (`reports/validate_repo.md`).
- API benchmarks (11.10.2025): `/v1/nodes` ? 12.4???, `/v1/moderation/cases` ? 18.6???, `/v1/notifications` ? 9.8??? (`var/api-benchmarks.json`).
- Import linter: нарушений не найдено (`var/backend-import-lint.txt`).
### Волна 1 — Фронтенд
- **Слои и архитектура**: зафиксировать референтную схему `layout → pages → widgets/features → entities/shared`; прогнать dependency graph, составить список нарушений и план миграции.
- **Кодовые долги**: закрыть дубли пагинации, debounce, статусы (см. `frontend-audit.md`). Вынести общие хуки в `src/shared`.
- **Тайпчеки/линты**: устранить ошибки в `src/features/management/payments/components/PaymentsView.tsx` и других файлах из `typecheck.log`.
- **SEO/перф**: выполнить P5 (метатеги, lazy-load, critical CSS, prefetch), провести Lighthouse и задокументировать в `frontend-audit.md` + `homepage-seo-guidelines.md`.
- **Тесты и визу**: синхронизировать Vitest, Cypress, Chromatic; проверить, что UI-примитивы закрывают все страницы.
- **Задачи Wave-1**: см. `docs/wave-1-tasks.md` для подробных описаний (DoR/DoD/AC).

### Волна 2 — Бэкенд
- **Доменные границы**: W2-1 — фасады `domains.platform.{iam,events,telemetry,audit,media}` и контракт importlinter `forbid_product_to_platform_facades` закрывают прямые импорты product→platform.
- **Типизация и линтеры**: обработать 79 ошибок из `mypy.log` (например, `Cannot assign to a method` в `domains/platform/moderation/application/service.py`).
- **Бизнес-логика**: анализ горячих путей (nodes, moderation, notifications) на предмет дублирования и нарушений SRP.
- **API фронта**: W2-6 — фронтовые клиенты nodes/moderation/notifications обновлены под Wave 2 OpenAPI (Vitest сценарии синхронизированы).
- **Производительность**: профилировать async операции, проверить индексы и кеши (redis, postgres), зафиксировать планы по оптимизации.
- **W2-4 async pipeline**: flamegraph в "var/profiling/", индексы из миграции "0110_nodes_notifications_indexes.py", Redis-кеш "product:nodes" (TTL 300s, лимит 5k записей), шаги и триггеры задокументированы в "docs/performance-playbook.md".
- **Безопасность**: CSRF двойная отправка (`issue_csrf_token` + `csrf_protect`), централизованный конфиг `infra/security/rate_limits.py` для публичных маршрутов, `SecretStr` в `packages.core.config.Settings`, тесты `test_security_csrf`/`test_security_rate_limit`, аудит `.env` и fallback настроек; W2-7 — фронт читает имена cookie/header из настроек, учитывает TTL CSRF, показывает глобальные тосты и повторяет запросы после 429 (Vitest/Cypress покрытие).

### Волна 3 — Инфраструктура и процессы
- **CI/CD**: убедиться, что lint/typecheck/pytest/coverage выполняются на PR, добавить missing checks (bandit, vulture, pip-audit, sbom) при необходимости.
- **Environment & Observability**: проверить docker-compose профили, OTEL (`infra/observability/opentelemetry.py`), alerting.
- **Документация/ADR**: обновить ADR по архитектурным границам, зафиксировать новые стандарты ревью, код-стайл, SLA багов.
- **Операционные процессы**: расписать роллбек-процедуры, smoke чек-листы, план стресс-тестов.

## Фронтенд: контроль слоев
- Настроить lint-правила для `@ui`, `@shared`, `features`, `entities` (расширить ESLint либо добавить custom rule).
- Перенести оставшиеся импорты из `vendor`/template в `src/shared/ui`.
- Составить dependency map и action plan по пересечениям (с приоритетами P0–P3).
- Результаты dependency map: см. `docs/frontend-dependency-report.md` (6 импортов features → pages; импорты из `vendor/*` не найдены, отчёты лежат в `var/frontend-deps`).

## Бэкенд: контроль доменов
- Использовать `importlinter` (layers + forbidden rules) и расширить покрытия на новые домены (ai, premium, worlds).
- Документировать контракт взаимодействий product ↔ platform, определить фасады/события для проблемных точек.
- Проверить `packages/` на предмет бизнес-логики (должна лежать в доменах) и вынести shared инфраструктуру.

## Инструменты и автоматизация
- Фронт: ESLint, TypeScript strict, Vitest, Cypress, Chromatic, Lighthouse CI (опционально Qodana).
- Бэк: Ruff, Black, Mypy (strict), Pytest (+ slow), Import Linter, Bandit, Vulture, Coverage, OpenAPI генерация.
- Общие: восстановить `scripts/validate_repo.py`, добавить make-цели и Github Actions шаги для новых проверок, вести журналы метрик в `var/`.

## Риски и защитные меры
- Любые правки структур — через feature-ветки + автотесты; предусмотреть smoke-чек после каждого мержа.
- Для миграций и refactor’ов — описывать план отката и тесты в задачах.
- Следить за кодировками (уже есть проблемы в некоторых md/tsx), привести файлы к UTF-8.

## Формирование backlog и ADR
- На основе каждой волны фиксировать issues в формате: модуль → проблема → метрика/лог → предложение → приоритет/оценка.
- Итоги волны документировать в ADR (шаблон: «Решение по фронтенд слоям», «Решение по доменным границам»).
- Обновлять `frontend-audit.md` и `backend-testing-strategy.md`, добавляя новые чек-листы и результаты.

### Wave 0 — backlog качества
- Фронтенд > Перфоманс главной и dev-blog ниже целевых 85 (61/73) > `var/lighthouse-home.json`, `var/lighthouse-devblog.json` > Оптимизировать hero-блоки, включить lazy-loading тяжёлых виджетов и проверить кеширование перед стартом Wave-1 > P1 / 3 дня
- Фронтенд > Размер entry-бандла 1.84 MB превышает лимит 1.2 MB > `var/frontend-bundle.json` > Вынести Quill и markdown-preview в отдельные чанки, настроить динамический импорт vendor-пакетов > P1 / 2 дня
- Бэкенд > Покрытие pytest 82.83% против цели 85% > `coverage.xml`, `var/coverage-summary.json` > Добавить тесты для `api_gateway.debug` и домена navigation, закрыть критические ветки до Wave-1 > P1 / 2 дня
- Бэкенд > Bandit падает на B110/B105/B311 > `reports/validate_repo.md` > Сузить перехваты исключений в `core.*`, заменить случайный jitter на детерминированный бэкофф или `secrets`-генератор > P2 / 1 день
- Платформа.navigation > API-бенчмарки падают с AttributeError по `NavigationService` > `var/api-benchmarks.json` > Восстановить `NavigationService` в контейнере или адаптировать мок, добавить smoke-тест `nodes:list` > P0 / 1 день



