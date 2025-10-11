# Wave 1 — задачи качества

## Задача W1-1 — Восстановить NavigationService и smoke API
- **Описание**: исправить падения `scripts/api_benchmark.py` (AttributeError по `NavigationService`) и зафиксировать рабочий smoke-тест `nodes:list`/`moderation:cases`.
- **Шаги выполнения**:
  1. Проанализировать `apps/backend/domains/product/navigation/application/service.py` и DI-сборку (`apps/backend/app/api_gateway/container_registry.py`, `wires.py`) на предмет отсутствующих экспортов.
  2. Реализовать/восстановить `NavigationService` и зарегистрировать его в контейнере, учесть зависимости (репозитории, кэши).
  3. Обновить API use-case, чтобы `GET /v1/nodes` и `GET /v1/moderation/cases` получали данные без заглушек.
  4. Дополнить smoke-тест (`tests/smoke` или `apps/backend/domains/product/navigation/tests/`) проверкой `nodes:list`, прогнать `scripts/api_benchmark.py`.
  5. Зафиксировать актуальный `var/api-benchmarks.json` и приложить вывод в Slack #backend-quality.
- **Определение готовности (DoR)**: есть доступ к staging БД/фейковым данным, подтверждена схема DI, согласован формат отчёта с @a.egorov и @svetlana.t.
- **Определение завершения (DoD)**: бенчмарки завершаются без ошибок, smoke-тесты проходят в CI, документация обновлена (`docs/backend-testing-strategy.md`).
- **Критерии приемки (AC)**:
  - `scripts/api_benchmark.py` возвращает 2xx и реальную латентность < 500 мс для `nodes:list`/`moderation:cases`.
  - Новый/обновлённый smoke-тест падает при регрессии `NavigationService`.
  - В отчёте Wave-1 добавлена ссылка на обновлённый `var/api-benchmarks.json`.
- **Артефакты**: `var/api-benchmarks.json`, `tests/smoke/test_navigation.py` (или аналогичный файл), сообщение в #backend-quality.

## Задача W1-2 — Поднять Lighthouse score до целевых 85+
- **Описание**: повысить мобайл Lighthouse performance главной и dev-blog до ≥85, сохранив SEO и UX показатели.
- **Шаги выполнения**:
  1. Переснять Lighthouse (`npm run build && npm run preview`, `npx lighthouse ...`) и выделить ключевые метрики (LCP, TBT, resource summary).
  2. Оптимизировать hero-блоки: lazy-load тяжёлых изображений/виджетов, настроить `loading="lazy"`, вынести некритичные скрипты.
  3. Проверить кеширование статических ресурсов и `prefetch` критических API (обновить `apps/web/src/shared/utils/prefetch.ts`).
  4. Перепроверить SEO-маркеры (title, meta, hreflang) совместно с маркетингом.
  5. Зафиксировать обновлённые отчёты в `var/lighthouse-home.json`, `var/lighthouse-devblog.json` и описать изменения в `apps/web/frontend-audit.md`.
- **Определение готовности (DoR)**: доступен макет/контент, подтверждён список KPI (performance, LCP, SEO), есть время QA на мобайл тестирование, согласованы риски с @irina.m.
- **Определение завершения (DoD)**: Lighthouse ≥85 (performance) и ≥95 (SEO), нет падений unit/Vitest, изменения задокументированы, согласование с маркетингом получено.
- **Критерии приемки (AC)**:
  - `var/lighthouse-home.json` и `var/lighthouse-devblog.json` содержат performance score ≥ 0.85 и LCP ≤ 2.5s.
  - В `apps/web/frontend-audit.md` добавлено описание оптимизаций и дата обновления.
  - В Slack #web-platform опубликован weekly отчёт со скриншотом/сводкой.
- **Артефакты**: `var/lighthouse-home.json`, `var/lighthouse-devblog.json`, diff в `apps/web/frontend-audit.md`.

## Задача W1-3 — Сократить entry bundle до ≤1.2 MB
- **Описание**: уменьшить размер стартового JS-чанка до согласованного лимита за счёт код-сплиттинга и оптимизации зависимостей.
- **Шаги выполнения**:
  1. Проанализировать `var/frontend-bundle.json` и отчёт Vite (`npm run build:client --report`) на предмет крупных модулей.
  2. Вынести редактор (Quill/markdown) и тяжёлые vendor-пакеты в динамические чанки/async-компоненты.
  3. Настроить `prefetch`/`preload` только для критичного кода, пересобрать проект и проверить SSR.
  4. Обновить e2e/Vitest тесты, чтобы учесть динамический импорт.
  5. Переснять bundle отчёт, приложить результаты к PR и задокументировать изменения.
- **Определение готовности (DoR)**: подтверждён список критичных маршрутов, согласован план сплиттинга с @george.n, тестовый стенд готов к проверке.
- **Определение завершения (DoD)**: entry bundle ≤1.2 MB (из `var/frontend-bundle.json`), нет регрессий SSR/e2e, документация и CI обновлены.
- **Критерии приемки (AC)**:
  - `var/frontend-bundle.json` показывает `Length` стартового чанка < 1_200_000 байт.
  - Добавлены lazy-чанки и префетч настроен через `usePrefetchLink`/`prefetch.ts`.
  - В PR приложен скрин/репорт build:client, QA подтвердил отсутствие визуальных регрессий.
- **Артефакты**: `var/frontend-bundle.json`, build report (`var/frontend-bundle-report.html` или аналог), заметки в `apps/web/frontend-audit.md`.

## Задача W1-4 — Поднять coverage backend до ≥85%
- **Описание**: закрыть дефицит покрытия (82.83% → ≥85%), уделив внимание `apps/backend/app/api_gateway/debug.py` и домену navigation.
- **Шаги выполнения**:
  1. Изучить `coverage.xml`/`var/coverage-summary.json`, найти файлы с низким покрытием (debug router, navigation use-cases).
  2. Добавить unit/contract тесты в соответствующих каталогах (`tests/unit`, `domains/product/navigation/tests`).
  3. Актуализировать fixtures/mocks, чтобы тесты не требовали боевых сервисов.
  4. Запустить `pytest -c apps/backend/pytest.ini --cov`, убедиться в росте метрики, обновить `coverage.xml`.
  5. Внести результаты в `docs/backend-testing-strategy.md` и опубликовать сводку в #backend-quality.
- **Определение готовности (DoR)**: готовы сценарии из продуктовой команды, доступен свежий `coverage.xml`, согласованы приоритеты тестирования с @svetlana.t.
- **Определение завершения (DoD)**: покрытие ≥85% (общий показатель) и ≥80% по домену navigation, тесты зелёные в CI, документация обновлена.
- **Критерии приемки (AC)**:
  - `coverage.xml` и `var/coverage-summary.json` фиксируют ≥85%.
  - Все новые тесты проходят локально и в CI без xfail/skip.
  - В `docs/backend-testing-strategy.md` указана дата обновления метрики.
- **Артефакты**: `coverage.xml`, `var/coverage-summary.json`, diff тестов.

## Задача W1-5 — Починить Bandit (B110/B105/B311)
- **Описание**: устранить предупреждения безопасности в `apps/backend/packages/core/*` и `worker.base`, восстановив зелёный `scripts/validate_repo.py`.
- **Шаги выполнения**:
  1. Проанализировать Bandit отчёт (`reports/validate_repo.md`), согласовать план правок с владельцами пакетов.
  2. Заменить `try/except: pass` на явную обработку/логирование, внедрить guard-кейсы.
  3. Для jitter использовать безопасный генератор (`random` → `secrets` или детерминированный backoff), пересмотреть хранение `"*"` токена.
  4. Запустить `scripts/validate_repo.py`, убедиться в зелёном статусе, обновить отчёт.
  5. Обновить документацию (`CodeValidator.md`) и сообщить об изменениях в #backend-quality.
- **Определение готовности (DoR)**: доступы к коду пакетов подтверждены, согласовано окно для refactor, известны ожидания DevSecOps.
- **Определение завершения (DoD)**: Bandit проходит без ошибок, другие проверки (ruff/mypy) не деградируют, документация актуальна.
- **Критерии приемки (AC)**:
  - `reports/validate_repo.md` фиксирует Bandit Exit Code 0.
  - В коде нет silent `except: pass` без логов, jitter реализован безопасно.
  - В PR приложен вывод `scripts/validate_repo.py`.
- **Артефакты**: `reports/validate_repo.md`, diff пакета `apps/backend/packages/core/*`, сообщение в #backend-quality.
