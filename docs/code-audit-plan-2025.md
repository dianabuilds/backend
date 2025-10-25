# План аудита кодовой базы (октябрь 2025)

## Обзор
- Провести сквозной аудит фронтенда (`apps/web`), бэкенда (`apps/backend`), инфраструктуры и процессов без потери стабильности.
- Выявить дубли, мёртвый код, нарушения архитектурных границ, проблемы безопасности и производительности.
- Сформировать очередь задач, ADR-решений и метрик для сопровождения до конца 2025 года.

### Охват
- Фронтенд: слойность, производительность, UX.
- Бэкенд: доменные границы, типизация, асинхронные пайплайны, безопасность.
- Инфраструктура: CI/CD, мониторинг, хранение секретов.

## Исходные артефакты
### Архитектура и документация
- `README.md`, `apps/backend/ARCHITECTURE.md`, `apps/web/README.md` — базовая карта сервисов, слойность и правила работы с шаблоном.
- `apps/web/frontend-audit.md` — перечень дублей, устаревших компонентов и UX-проблем.
### Качество и CI
- Логи CI: `typecheck.log`, `mypy.log`, `coverage.xml` — фиксация текущих ошибок типов и покрытия (82.83% по moderation repos).
- CI/CD конфигурации: `.github/workflows/ci.yml`, `ci-nightly.yml`, `docs.yml` — автоматизация линтов, типизации, генерации схем.
- Конфигурации качества: `pyproject.toml`, `eslint.config.js`, `vitest.config.ts`, `cypress.config.ts`, `qodana.yaml`.
### SEO и перформанс
- `apps/web/homepage-seo-guidelines.md`, ADR `adr/2025-10-09-homepage-configuration-tasks.md` (раздел P5).
- Метрики: `var/lighthouse-home.json`, `var/lighthouse-devblog.json`, `var/frontend-bundle.json`.

## Целевые критерии качества
| Направление | Цель | Метрики и инструменты |
|-------------|------|------------------------|
| Фронтенд | ESLint/Vitest без ошибок; Lighthouse score ≥ 85 (мобайл); контроль размера bundle; SSR/LCP ≤ 2.5 s на стенде | ESLint, Vitest, Lighthouse, Webpack bundle report |
| Бэкенд | mypy strict = 0 ошибок; Ruff clean; pytest (unit+integration) ≥ 85% по ключевым доменам; import-linter без нарушений | MyPy, Ruff, Pytest, Import Linter |
| Инфраструктура | CI ≤ 10 мин на PR; nightly slow-тесты стабильны; OpenAPI обновляется на каждый merge | GitHub Actions, nightly pipeline, экспорт OpenAPI |
| Безопасность | Секреты только в `.env` (валидация через `pydantic-settings`); bandit/vulture/pip-audit встроены в `scripts/validate_repo` | Bandit, Vulture, Pip Audit, `scripts/validate_repo.py` |

## Структура волн
| Волна | Фокус | Основные deliverables | Связанные документы |
|-------|-------|-----------------------|---------------------|
| Волна 0 — Подготовка | Сбор карты зависимостей, восстановление валидаций, фиксация метрик | Dependency map, обновлённый `scripts/validate_repo.py`, baseline Lighthouse/coverage/API | Этот файл, `docs/frontend-dependency-report.md`, `var/*` |
| Волна 1 — Фронтенд | Контроль слоя `layout → pages → widgets/features → entities/shared`, оптимизация UX/SEO, единая библиотека тестов | ESLint правило для слоёв, обновлённый `src/shared`, отчёты Lighthouse/Chromatic | `apps/web/frontend-audit.md`, `apps/web/homepage-seo-guidelines.md` |
| Волна 2 — Бэкенд | Доменные границы, типизация, производительность, безопасность API + фронтовые клиенты | Фасады product ↔ platform, mypy strict, оптимизированные hot-path, CSRF/429 защита | `docs/wave-2-backend.md`, `apps/backend/var/openapi.json` |

## Детализация волн
### Волна 0 — Подготовка
**Фокус:** актуализировать карту модулей и зависимости, собрать базовые метрики и восстановить валидаторы.

**Основные шаги:**
- Актуализировать карту модулей и зависимостей (madge/`eslint-plugin-boundaries` для фронта, `importlinter` снапшот для бэка).
- Восстановить или дописать `scripts/validate_repo.py` и обновить документацию `CodeValidator.md`.
- Собрать базовые метрики: Lighthouse отчёты, pytest coverage, время ответов API (httpx/builtin бенчмарки), размер бандла `@caves/web`.
- Согласовать перечень целевых показателей и приемочных критериев с продуктом и безопасностью.

**Артефакты:** `docs/frontend-dependency-report.md`, `var/frontend-deps/*`, `scripts/validate_repo.py`, отчёты в `var/`.

#### Базовые метрики (октябрь 2025)
- Lighthouse performance (мобайл): home 0.61, dev-blog 0.73 (`var/lighthouse-home.json`, `var/lighthouse-devblog.json`).
- Lighthouse SEO: home 0.92 (цель 0.95) — требуется корректировка мета-тегов.
- Entry bundle (JS): 1.84 MB (`var/frontend-bundle.json`).
- pytest coverage: 82.83% общий показатель (`coverage.xml`, `var/coverage-summary.json`).
- Bandit: падение на B110/B105/B311 (`reports/validate_repo.md`).
- API benchmarks (11.10.2025): `/v1/nodes` ? 12.4???, `/v1/moderation/cases` ? 18.6???, `/v1/notifications` ? 9.8??? (`var/api-benchmarks.json`).
- Import linter: нарушений не найдено (`var/backend-import-lint.txt`).

### Волна 1 — Фронтенд
**Фокус:** наведение порядка в слоях, устранение дублей, производительность и визуальная регрессия.

**Основные блоки:**
- Слои и архитектура: зафиксировать схему `layout → pages → widgets/features → entities/shared`; прогнать dependency graph, составить список нарушений и план миграции.
- Кодовые долги: закрыть дубли пагинации, debounce, статусы (см. `frontend-audit.md`); вынести общие хуки в `src/shared`.
- Тайпчеки и линты: устранить ошибки в `src/features/management/payments/components/PaymentsView.tsx` и других файлах из `typecheck.log`.
- SEO/перф: выполнить P5 (метатеги, lazy-load, critical CSS, prefetch), провести Lighthouse и задокументировать в `frontend-audit.md` и `homepage-seo-guidelines.md`.
- Тесты и визу: синхронизировать Vitest, Cypress, Chromatic; проверить, что UI-примитивы покрывают все страницы.

**Артефакты:** `apps/web/frontend-audit.md`, `docs/frontend-dependency-report.md`, обновлённые ESLint конфиги и отчёты Lighthouse/Chromatic.

### Волна 2 — Бэкенд
**Фокус:** доменные границы, типизация, горячие сценарии и безопасность API совместно с фронтом.

**Ключевые направления:**
- Выстроить фасады между product и platform, зафиксировать правила в `importlinter`.
- Закрыть 79 ошибок mypy strict и обновить `docs/backend-testing-strategy.md`.
- Разгрузить hot-path use-case nodes/moderation/notifications и оптимизировать async pipeline/хранение.
- Усилить безопасность: CSRF, rate-limit, секреты, синхронизировать обновления с фронтом (сценарии CSRF/429).

**Подробная декомпозиция:** `docs/wave-2-backend.md` (карта задач, DoR/DoD и история внедрений).

## Рабочие потоки по направлениям
### Фронтенд — контроль слоёв
- Настроить lint-правила для `@ui`, `@shared`, `features`, `entities` (расширить ESLint либо добавить custom rule).
- Перенести оставшиеся импорты из `vendor`/template в `src/shared/ui`.
- Составить dependency map и action plan по пересечениям (приоритеты P0–P3).
- Отчёты dependency map: `docs/frontend-dependency-report.md` (6 импортов features → pages; импорты из `vendor/*` не найдены, данные в `var/frontend-deps`).

### Бэкенд — контроль доменов
- Использовать `importlinter` (layers + forbidden rules) и расширить покрытия на новые домены (`ai`, `premium`, `worlds`).
- Документировать контракт взаимодействий product ↔ platform, определить фасады/события для проблемных точек.
- Проверить `packages/` на предмет бизнес-логики и вынести shared инфраструктуру в отдельные слои.

## Инструменты и автоматизация
| Направление | Инструменты | Комментарии |
|-------------|-------------|-------------|
| Фронтенд | ESLint, TypeScript strict, Vitest, Cypress, Chromatic, Lighthouse CI, Qodana (опционально) | Уточнить правила для слоёв и производительности |
| Бэкенд | Ruff, Black, MyPy (strict), Pytest (+ slow), Import Linter, Bandit, Vulture, Coverage, OpenAPI генерация | Синхронизировать с `scripts/validate_repo.py` и nightly |
| Общие | `scripts/validate_repo.py`, make-цели, GitHub Actions шаги, метрики в `var/` | Восстановить единый валидатор и добавить новые проверки |

## Риски и защитные меры
- Структурные правки — через feature-ветки + автотесты; после каждого мержа выполнять smoke-check.
- Для миграций и refactor’ов заранее описывать план отката и тесты в задачах.
- Следить за кодировками (обнаружены проблемы в отдельных md/tsx), привести файлы к UTF-8.

## Формирование backlog и ADR
- На основе каждой волны фиксировать issues в формате «модуль → проблема → метрика/лог → предложение → приоритет/оценка».
- Итоги волн документировать в ADR (шаблоны: «Решение по фронтенд слоям», «Решение по доменным границам»).
- Обновлять `frontend-audit.md` и `backend-testing-strategy.md`, добавляя чек-листы и результаты.

### Wave 0 — backlog качества
| Направление | Проблема | Метрика/Источник | Предложение | Приоритет / оценка |
|-------------|----------|------------------|-------------|--------------------|
| Фронтенд | Перфоманс главной и dev-blog ниже целевых 85 (61/73) | `var/lighthouse-home.json`, `var/lighthouse-devblog.json` | Оптимизировать hero-блоки, включить lazy-loading тяжёлых виджетов, проверить кеширование до старта Волны 1 | P1 / 3 дня |
| Фронтенд | Размер entry-бандла 1.84 MB превышает лимит 1.2 MB | `var/frontend-bundle.json` | Вынести Quill и markdown-preview в отдельные чанки, настроить динамический импорт vendor-пакетов | P1 / 2 дня |
| Бэкенд | Покрытие pytest 82.83% против цели 85% | `coverage.xml`, `var/coverage-summary.json` | Добавить тесты для `api_gateway.debug` и домена navigation, закрыть критические ветки до Волны 1 | P1 / 2 дня |
| Бэкенд | Bandit падает на B110/B105/B311 | `reports/validate_repo.md` | Сузить перехваты исключений в `core.*`, заменить случайный jitter на детерминированный backoff или `secrets`-генератор | P2 / 1 день |
| Платформа.navigation | API-бенчмарки падают с AttributeError по `NavigationService` | `var/api-benchmarks.json` | Восстановить `NavigationService` в контейнере или адаптировать мок, добавить smoke-тест `nodes:list` | P0 / 1 день |
