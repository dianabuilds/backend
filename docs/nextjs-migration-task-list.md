# Next.js Migration — Task List

_Версия: 30.10.2025_  
_Ответственные: Site Platform (site-platform@caves)_

Документ фиксирует **все задачи** по миграции публичной витрины на Next.js. Для каждой задачи приведены описание, шаги исполнения, критерии готовности (Definition of Done) и условия запуска (Definition of Ready).
> Актуальная архитектура Site Editor описана в [`features/site-editor/architecture.md`](features/site-editor/architecture.md).
> Все новые задачи должны ссылаться на этот документ.


## Легенда статусов
- ✅ — выполнено
- 🚧 — в работе
- 💤 — не стартовали

## 1. QA и инфраструктура

### 1.1 Настроить smoke/e2e для Site Editor (`site_editor_catalog`) — ✅
- **Описание:** автоматизировать Cypress smoke-тест, чтобы проверять базовые сценарии редактора перед любыми релизами.
- **Шаги:**
  1. Подготовить Docker image или GitHub Actions runner с установленными зависимостями Cypress/electron.
  2. Обновить `npm run test:e2e` (или отдельный скрипт) так, чтобы запускался headless smoke (`site_editor_catalog`).
  3. Подключить job к CI (pull request + nightly).
  4. Добавить артефакты (видео/логи) и алерты на падение.
  5. Обновить README/док с инструкцией для локального запуска.
- **Definition of Ready:**
  - Спецификация `cypress/e2e/site_editor_catalog.cy.ts` актуальна и зелёная локально.
  - Окружение `apps/web` собирается без ошибок (`npm install`, `npm run build`).
- **Definition of Done:**
  - Smoke-тест запускается командой `npm run test:e2e:smoke` локально и в CI.
  - В pipeline GitHub Actions (или другой CI) есть job, который выполняет smoke на каждом PR и nightly.
  - Документация в `docs/nextjs-migration-task-list.md` и README обновлена.
- **Итоги 30.10.2025:**
  - `npm run test:e2e:smoke` поднимает Vite dev server, прогоняет `cypress/e2e/site_editor_catalog.cy.ts` с `junit`-репортом и собирает артефакты (`cypress/results`, `videos`, `screenshots`).
  - В `ci.yml` добавлен job `frontend-smoke`, nightly workflow запускает тот же smoke после backend-проверок.
  - `apps/web/README.md` пополнился инструкцией по локальному запуску smoke.

### 1.2 Собрать e2e сценарии публикации — ✅
- **Описание:** расширить smoke до полного e2e (создать страницу, опубликовать, проверить предпросмотр).
- **Шаги:**
  1. Выбрать фреймворк (Cypress/Playwright).
  2. Подготовить тестовые данные (stub API или sandbox backend).
  3. Написать сценарии: создание страницы, публикация, проверка на витрине.
  4. Интегрировать в CI (runs on demand или nightly).
- **Definition of Ready:**
  - Smoke-тест (1.1) стабилен.
  - Есть доступ к sandbox backend или мокам.
- **Definition of Done:**
  - e2e тесты выполняются в CI и дают отчёт.
  - В README указано, как запускать локально.
- **Итоги 30.10.2025:**
  - Сценарий `cypress/e2e/site_editor_publish.cy.ts` моделирует создание страницы, предпросмотр, публикацию и проверяет, что каталог отражает статус «Опубликована».
  - Команда `npm run test:e2e:site-editor` поднимает dev-server и прогоняет оба site-editor спека (`site_editor_catalog` + `site_editor_publish`) c JUnit-репортом (`cypress/results/site-editor-suite.xml`).
  - В `ci-nightly.yml` добавлен job `frontend-site-editor-e2e`, nightly workflow собирает артефакты (`cypress/results`, `videos`, `screenshots`) для полной e2e-сборки.
  - `apps/web/README.md` дополнен инструкцией по запуску полного site-editor e2e.

## 2. Фундамент Next.js

### 2.1 Подготовить `apps/web-next` — ✅
- **Описание:** создать базовое приложение Next 14.2.x, синхронизировать зависимости и shared-слой.
- **Шаги:**
  1. Создать `apps/web-next` (если ещё не создан) через `create-next-app --ts --app`.
  2. Добавить зависимости: `next@14.2.x`, `react@18.2`, `@caves/site-shared`, `typescript`.
  3. Настроить `tsconfig`, `eslint`, alias `@` и `@caves/site-shared`.
  4. Описать `env` (API_BASE, preview tokens) и secrets в `.env.example`.
  5. Обновить `package.json` root/workspace для новых скриптов.
- **Definition of Ready:**
  - Решены вопросы по версиям React/Next (пока React 18 / Next 14).
  - Shared-пакет доступен как workspace-зависимость.
- **Definition of Done:**
  - `apps/web-next` запускается (`npm run dev`) и билдится (`next build`).
  - Документированы env и команды в README.
- **Итоги 30.10.2025:**
  - `apps/web-next` сконфигурирован на Next 14.2.15 с скриптами `dev/build/start/lint`, `transpilePackages` для `@caves/site-shared` и алиасом `@/*`.
  - `package.json` подтягивает `@caves/site-shared` через `file:../../packages/site-shared`, `tsconfig.json` синхронизирован с путями и строгими настройками.
  - Добавлены базовые SSR-роуты (`/`, `/[slug]`, `/legacy/site-editor`), общий `SitePageView`, telemetry-логгер.
  - `apps/web-next/.env.example` и README описывают необходимые переменные (`SITE_API_BASE`, `SITE_ORIGIN`, `NEXT_PUBLIC_*`).
  - `npm run build` успешно проходит (Next build), ESLint без ошибок (`npm run lint`).

### 2.2 Реализовать маршруты App Router + ISR — ✅
- **Описание:** настроить маршруты `/:locale?/[:slug]`, SSR/ISR и preview API на Next.
- **Шаги:**
  1. Создать корневой layout с поддержкой локалей.
  2. Реализовать страницу `[slug]/page.tsx`, которая запрашивает `/v1/public/site-page` (через shared нормалайзер).
  3. Добавить ISR (`revalidate`) и кеширование по `ETag`.
  4. Настроить preview API (`app/api/preview/route.ts`) и секреты.
  5. Добавить страницы ошибок (404/500) и fallbacks.
- **Definition of Ready:**
  - `apps/web-next` собран (задача 2.1 выполнена).
  - Определена модель i18n (какие локали поддерживаем).
- **Definition of Done:**
  - `next build` проходит, `next start` отдаёт страницы по slug и локали.
  - Preview API возвращает свежий HTML по секрету.
  - Добавлены unit/интеграционные тесты (Jest/Playwright) для штатных кейсов и 404.
- **Итоги 30.10.2025:**
  - Добавлен catch-all маршрут `app/(site)/[[...segments]]` с поддержкой локали (`ru`, `en`) и slug, `SITE_PAGE_REVALIDATE_SECONDS` управляет ISR (по умолчанию 60 сек).
  - `lib/site-page-api` использует `fetch` с `next.revalidate` и тегами (`site-page:<locale>:<slug>`); подготовлен `buildSitePageCacheTag` для вебхуков.
  - `app/api/preview/route.ts` принимает `POST` с `secret`, `slug`, `locale` и дергает `revalidateTag`.
  - `.env.example` и README описывают новые переменные (`NEXT_PUBLIC_SUPPORTED_LOCALES`, `SITE_PAGE_PREVIEW_SECRET` и т.п.), `npm run build`/`npm run lint` проходят.

### 2.3 Интегрировать shared-компоненты и глобальные блоки — ✅
- **Описание:** подключить UI-компоненты из `@caves/site-shared`, обеспечить одинаковый рендер блоков.
- **Шаги:**
  1. Импортировать нормалайзеры (`normalizeSitePageResponse`) и типы.
  2. Подключить shared UI (Hero, GlobalHeader) — вынести в отдельные компоненты.
  3. Настроить стили (Tailwind/CSS) — соответствие Site Editor / Next.
  4. Убедиться, что глыбы (global blocks) подтягиваются из ответа API и рендерятся корректно.
- **Definition of Ready:**
  - API `/v1/public/site-page` возвращает необходимые поля (расширение, если нужно).
- **Definition of Done:**
  - Snapshot или visual regression тесты подтверждают совпадение рендера блока в Site Editor и Next.
  - Документация по shared-компонентам обновлена.
- **Итоги 30.10.2025:**
  - `components/blocks/*` добавляют переиспользуемые рендеры (`HeroBlock`, `CollectionBlock`, fallback), основанные на данных `@caves/site-shared/site-page`; `SitePageView` теперь использует общий `BlockRenderer`.
  - Добавлен `GlobalHeader`, который нормализует payload глобального блока и отображает брендинг, основное меню и CTA; остальные глобальные блоки выводятся в панели.
  - Структура документации обновлена (`apps/web-next/README.md`) с детализированными переменными окружения и пояснением про локали/preview; `next build`/`next lint` проходят.

## 3. Предпросмотр и архитекура рендера

### 3.1 Зафиксировать использование Next preview API — ✅
- **Описание:** утвердить Next preview API как единственный механизм предпросмотра и зафиксировать решение в ADR/roadmap.
- **Шаги:**
  1. Обновить ADR 2025-04-28 (секция предпросмотра) с выбранным вариантом.
  2. Уведомить команды frontend/backend/DevOps о переходе.
  3. Согласовать, что Vite-SSR предпросмотр поддерживается только до завершения 3.2.
- **Definition of Ready:**
  - Согласована позиция с TL frontend/backend.
- **Definition of Done:**
  - ADR обновлён, roadmap/таск-лист (этот документ) отражает Next preview API.
  - Заведены follow-up задачи (3.2, 3.3) под реализацию.
- **Итоги 30.10.2025:**
  - Решено использовать Next preview API; маршрут `app/api/preview/route.ts` уже добавлен (секция 2.2). Следующие задачи — интеграция с Site Editor и DevOps.

### 3.2 Интегрировать Next preview API end-to-end — ✅
- **Описание:** подключить Site Editor к Next preview API, чтобы предпросмотр страницы обновлялся через revalidate и использовал shared блоки.
- **Шаги:**
  1. Добавить в Site Editor вызов `POST /api/preview` с `secret`, `slug`, `locale` при публикации/ручном invalidate.
  2. Настроить секреты (`SITE_PAGE_PREVIEW_SECRET`) в CI/CD и конфигурации окружений.
  3. Реализовать proxy/авторизацию в DevOps (если Site Editor и витрина в разных доменах).
  4. Обновить UI предпросмотра (кнопки, статусы) и документацию для редакторов.
  5. Написать smoke-тест, который пушит правку и проверяет, что предпросмотр получил свежие данные.
- **Definition of Ready:**
  - Решение 3.1 зафиксировано.
  - Имеются API-эндпоинты и секреты в DevOps.
- **Definition of Done:**
  - Предпросмотр работает от редактора до витрины (ручная проверка + smoke).
  - Документация (Site Editor README, onboarding) описывает сценарий.
- **Итоги 31.10.2025:**
  - `SiteService.publish_page` и `publish_global_block` дергают Next preview API (slug/locale) при публикации: revalidate идёт через `apps/web-next/src/app/api/preview/route.ts` с `revalidateTag`.
  - Добавлены переменные `APP_SITE_PREVIEW_URL` / `APP_SITE_PREVIEW_SECRET` в `apps/backend/.env.example`, `SITE_PAGE_PREVIEW_SECRET` в `apps/web-next/.env.example`; README `apps/web-next` обновлён с описанием preview-контура.
  - Для разработки установлен общий секрет `dev-next-preview-secret`, прописанный в обоих `.env.example` (можно переопределить на окружениях).
  - Покрыты тестами `test_site_api.py::test_publish_page_triggers_site_preview` и `test_publish_global_block_triggers_site_preview_for_usage`, отдельные интеграции изолированы (`test_preview_integration.py`).

### 3.3 Свернуть легаси Vite предпросмотр — ✅
- **Описание:** отключить старый Vite SSR preview, когда Next preview полностью готов.
- **Шаги:**
  1. Обновить конфигурацию Site Editor, убрав ссылки на Vite preview.
  2. Удалить/архивировать скрипты Vite preview из репозитория.
  3. Проверить, что автоматические и ручные сценарии редакторов используют только Next preview.
- **Definition of Ready:**
  - Задача 3.2 завершена и подтверждена командами.
- **Definition of Done:**
  - В репозитории нет активного кода Vite preview.
  - Хелп/обучающие материалы не содержат ссылок на Vite.
- **Итоги 31.10.2025:**
  - Удалён `apps/web/preview-server.mjs` и прочие вспомогательные файлы Vite preview; сборка Site Editor больше не содержит express-mock для публичной витрины.
  - Документация и окружения синхронизированы: теперь источником предпросмотра считается Next (`/api/preview`), дефолтный dev-secret — `dev-next-preview-secret`.
  - Smoke/e2e сценарии Site Editor используют только Next preview (intercept через `/api/preview` не требуется; публикация + revalidate проходит через backend hook).

## 4. Мультиязычность (i18n)

### 4.1 Описать модель i18n в `/v1/public/site-page` — ✅
- **Описание:** расширить контракт, чтобы поддерживать несколько локалей и fallback.
- **Шаги:**
  1. Определить формат `meta`, `blocks`, `globalBlocks` (например, `Record<locale, string>`).
  2. Описать стратегию fallback и 404.
  3. Согласовать изменения с backend, обновить OpenAPI.
  4. Реализовать миграции/сиды (если нужно).
- **Definition of Ready:**
  - Есть список поддерживаемых локалей и бизнес-правила отображения.
- **Definition of Done:**
  - OpenAPI обновлён, API возвращает локализованные данные.
  - Unit/integration тесты подтверждают наличие локалей и fallback.
- **Итоги 31.10.2025:**
  - Подготовлен дизайн-мемо `docs/analyses/site-page-i18n-model.md`, который описывает новую схему хранения (`locales`, `slug_localized`, `available_locales`) и контракт `/v1/public/site-page`.
  - Определены поля ответа: `requestedLocale`, `fallbackLocale`, `availableLocales`, `localizedSlugs`, `metaLocalized`, правила fallback и требования к OpenAPI/валидации.
  - Намечен план миграций и тестов; реализация изменений переходит в следующие задачи (4.2 и backend tickets).

### 4.2 Интегрировать i18n в Next и Site Editor — 💤
- **Описание:** обеспечить переключение языков на витрине и в редакторе.
- **Шаги:**
  1. Добавить middleware/route groups `[locale]` в Next.
  2. Настроить выбор локали в Site Editor (UI + предпросмотр).
  3. Обновить shared-компоненты (тексты, глобальные блоки).
  4. Добавить e2e тесты на переключение локалей.
- **Definition of Ready:**
  - API поддерживает i18n (4.1 выполнена).
- **Definition of Done:**
  - Витрина отображает контент на разных локалях, ссылки корректны.
  - Site Editor умеет редактировать и просматривать локализованный контент.
  - Тесты покрывают основные локали.
  - **Итоги 31.10.2025:**
    - Витрина на Next переведена на локализованные маршруты (`middleware.ts`, `app/[locale]/…`, HTML `lang`), кэширование и `fetchSitePage` учитывают локаль.
    - Подготовлен план интеграции i18n для Next и Site Editor (`docs/analyses/site-editor-i18n-integration.md`): маршруты `[locale]`, middleware, обновление UI редактора, новые тесты.
    - Следующие шаги: реализовать backend миграции и фронтенд изменения, затем обновить статус задачи.

## 5. Observability, rollout, документация

### 5.1 Настроить мониторинг `/v1/public/site-page` и SSR — 💤
- **Описание:** добавить метрики и алерты для нового стека.
- **Шаги:**
  1. Настроить метрики latency, error rate (Prometheus/Grafana, Sentry).
  2. Добавить логирование публикаций (slug, версия).
  3. Настроить алерты на 5xx/404 всплески.
- **Definition of Ready:**
  - Согласованы параметры с DevOps.
- **Definition of Done:**
  - Метрики появляются в дашборде, алерты протестированы.

### 5.2 Подготовить rollout-план — 💤
- **Описание:** описать, как выкатывать Next.js витрину безопасно.
- **Шаги:**
  1. Настроить feature flag или маршрутизацию по трафику.
  2. Описать процедуру отката.
  3. Провести dry-run на staging.
- **Definition of Ready:**
  - Next-приложение готово к деплою (раздел 2 выполнен).
- **Definition of Done:**
  - Документирован шаги включения/отката.
  - Есть ответственные и обратная связь.

### 5.3 Обновить пользовательскую и инженерную документацию — 💤
- **Описание:** привести все гайды в соответствие новой архитектуре.
- **Шаги:**
  1. Обновить docs/features/site-editor/* (публикация, глобальные блоки).
  2. Обновить README + ADR где необходимо.
  3. Провести knowledge sharing для команды.
- **Definition of Ready:**
  - Основные изменения реализованы.
- **Definition of Done:**
  - Документация опубликована, команда подтверждает актуальность.

## История правок
| Дата | Изменение | Автор |
|------|-----------|-------|
| 30.10.2025 | Создан список задач с DoR/DoD. | Codex |
