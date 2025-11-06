# План интеграции i18n для Next витрины и Site Editor

Дата: 31.10.2025

## 1. Текущее состояние

### 1.1 Next (`apps/web-next`)
- Доступен catch-all маршрут `/(site)/[[...segments]]`, сам вручную парсит первый сегмент как локаль (`ru`/`en`), но:
  - нет route groups `[locale]` и middleware → canonical URL `/slug` и `/en/slug` обрабатываются одинаково, SSR заголовки фиксированы на `lang="en"`.
  - HTML `<html lang>` всегда `en`, `metadataBase` не переключается, ссылки `<link rel="alternate">` не формируются автоматически.
  - `buildMetadataForPage` берёт `page.meta` без явной поддержки `metaLocalized`.
  - Кэш тегов (`revalidateTag`) не учитывает локаль — invalidate по slug затрагивает все локали одновременно.
- Конфиг `config/i18n.ts` читает `NEXT_PUBLIC_SUPPORTED_LOCALES`, но не синхронизирован с backend-списком.

### 1.2 Site Editor (`apps/web`)
- Страницы и глобальные блоки имеют одно поле `locale` (`ru`/`en`) и единый payload.
- Формы (`SitePageInfoPanel`, модальные создания страниц) позволяют выбрать только одну локаль → нет поддержки нескольких переводов.
- Предпросмотр `previewSitePage` отправляет POST `/v1/site/pages/{id}/preview` без контекста локали (кроме поля `locale` на странице).
- Каталог страниц не показывает наличие переводов; фильтр `locale` работает по одному значению.
- Нет UI для управления `availableLocales`/fallback, slug_per_locale, статусов локалей.

### 1.3 Backend
- Модель 4.1 подготовлена (см. `site-page-i18n-model.md`), но API пока возвращает single-locale документ.

## 2. Цели интеграции (задача 4.2)
1. Next витрина должна обслуживать URLs вида `/{locale}/…` + fallback на дефолт.
2. Site Editor должен управлять отдельными версиями страницы/блоков по локалям (создание, редактирование, публикация).
3. Предпросмотр и публикация должны работать с конкретной локалью и корректно вызывать `/api/preview`.
4. Smoke/e2e тесты должны проверять переключение локалей в vitrine и редакторе.

## 3. План работ

### 3.1 Backend (подготовка API)
- Реализовать модель из 4.1: поля `default_locale`, `available_locales`, `slug_localized`, структура `data/meta.locales`.
- Расширить `/v1/public/site-page`:
  - query-параметры `locale`, `fallback`.
  - поля ответа `requestedLocale`, `fallbackLocale`, `availableLocales`, `localizedSlugs`, `metaLocalized`.
  - `blocks`, `payload`, `globalBlocks` — локализованные с fallback.
- Обновить админ-API (`draft`, `publish`, `preview`) для работы с `locales`.
- Обновить OpenAPI/JSON Schema.

### 3.2 Next (`apps/web-next`)
1. **Маршруты и middleware**
   - Добавить `middleware.ts`, который перенаправляет `/slug` → `/<default-locale>/slug`, нормализует `Accept-Language` и хранит `NEXT_LOCALE` cookie.
   - Реорганизовать `app`:
     - `src/app/[locale]/[[...segments]]/page.tsx` для локализованных маршрутов.
     - Общий layout `src/app/[locale]/layout.tsx` → устанавливает `<html lang>`.
2. **Загрузка данных**
   - Обновить `getSitePage`/`fetchSitePageInternal` для передачи `locale` и работы с `requestedLocale`/`fallbackLocale`.
   - Обновить `renderSitePage` / `SitePageView` для отображения выбранной локали, списка доступных, fallback.
   - Ввести компонент переключателя локали (использует `availableLocales`, `localizedSlugs`).
3. **Metadata/SEO**
   - `buildMetadataForPage` генерирует `<link rel="alternate">`, `og:locale`, `og:locale:alternate`, `alternateLanguages`.
   - Скорректировать OG/Twitter заголовки, canonical (`localizedSlugs`).
4. **Кеширование**
   - Теги `revalidateTag` должны учитывать `locale`: `site-page:${locale}:${slug}`.
   - `/api/preview` принимает `locale` → уже передаётся.
5. **Testing**
   - Unit/Integration: mock fetch с несколькими локалями, ensure fallback behavior.
   - E2E (Playwright/Cypress): route `/en/...` и переключатель.

### 3.3 Site Editor (`apps/web`)
1. **Типы и API**
   - Обновить `SitePageSummary`, `SitePageDraft`, `SiteGlobalBlock` согласно новой схеме (`availableLocales`, `locales` payload).
   - HTTP-клиенты (`management/siteEditor/pages.ts`, `blocks.ts`) передают/принимают локализованные структуры.
2. **UI/UX**
   - Добавить переключатель локалей в редакторе страницы (вкладки/табличка). Возможность добавить новую локаль.
   - Формы редактирования slug/title/owner — per locale + global настройки.
   - Глобальные блоки: аналогичный UI для локалей.
   - В каталоге страниц отобразить «доступные локали», фильтры по ним, индикатор «не переведено».
3. **Предпросмотр/публикация**
   - `previewSitePage`/`publishPage` должны указывать, какую локаль публикуем (payload -> backend).
   - Hook `useSitePageEditorState` хранит состояние по локалям (draft map, dirty flags, review status).
4. **Smoke/e2e**
   - Расширить `site_editor_publish.cy.ts`: создать RU страницу, добавить EN перевод, проверить предпросмотр и публикацию, убедиться что витрина `/en/...` обновилась.
   - Добавить regression на fallback (EN отсутствует → отображаем RU).
5. **Документация**
   - Обновить README Site Editor в фронтенд-репозитории.
   - Зафиксировать изменения в `docs/features/site-editor/architecture.md`.

## 4. Зависимости и риски
- Реализация требует скоординированных миграций: Frontend нужно переключать после backend deployment.
- Потребуются миграции данных для существующих страниц/блоков.
- Надо заранее договориться о наборе локалей (initial: `ru`, `en`).
- Необходимо убедиться, что Next SSR и CDN корректно обрабатывают cookie `NEXT_LOCALE` и обходят кэш по локали.

## 5. Следующие шаги
1. Создать backend задачи: миграции БД, апдейты API, тесты (`domains/product/site` + `apps/backend/docs/openapi`).
2. Подготовить фронтовые задачи:
   - `apps/web-next`: middleware + `[locale]` routes.
   - `apps/web`: refactor редактора под локали.
3. Обновить CI pipelines (lint/test) для новых тестов.
4. После реализации — отметить задачу 4.2 завершённой и переходить к разделу 5.







