# Инвентаризация страниц и маршрутов (черновик)

Документ собирает актуальные страницы фронтенда и их связку с данными. Цель — облегчить миграцию публичной витрины на Next.js и отделение Site Editor. Фокус на витрине (SSR) и разделах админки, связанных с Site Editor и смежными модулями.

## 1. Контекст
- Фронтенд сейчас — монолит на Vite 5.4 (`apps/web/package.json`) с кастомным SSR через Express (`apps/web/server/createServer.ts`, `apps/web/src/entry-server.tsx`).
- Публичные маршруты ограничены витриной (`/`, `/:slug`) и dev-blog. Остальные запросы обслуживаются SPA-роутером.
- Админка и редактор блоков живут в том же приложении, доступ в приватные разделы ограничивается через `Guard` (`apps/web/src/routes/PrivateAppRoutes.tsx:89`).
- Переход на Next.js подразумевает перенос SSR/ISR и data-fetching на сервер, а также вынос предпросмотра в общий движок.

## 2. Публичные страницы (SSR)

| Маршрут | Компонент | Источник данных | SSR/предзагрузка | Примечания |
|---------|-----------|-----------------|------------------|------------|
| `/` | `HomePage` (`apps/web/src/pages/public/HomePage.tsx`) | `fetchSitePage('main')` → `/v1/public/site-page` | Да (через `entry-server.tsx`) | Использует slug `main` по умолчанию, кэшируется по `etag`.
| `/:slug` | `HomePage` | `fetchSitePage(slug)` | Да | Обрабатывает произвольные slug будущих страниц. Нужно обеспечить 404 и fallbacks.
| `/dev-blog` | `DevBlogListPage` | `fetchDevBlogList` → `/v1/public/dev-blog` | Да | Пагинация, фильтры по тегам и датам — query string.
| `/dev-blog/:slug` | `DevBlogPostPage` | `fetchDevBlogPost` → `/v1/public/dev-blog/{slug}` | Да | Возвращает 404 при отсутствии записи (см. `apps/web/src/pages/public/__tests__/ssr-server.test.ts`).
| `/n/:slug` | `NodePublicPage` | `apiGet('/v1/nodes/slug/{slug}')` | Нет (CSR) | Простая публичная страница узла, рендерится на клиенте.
| `*` | `RouteFallback` | — | Нет | Заглушка при отсутствии подходящего маршрута.

### Наблюдения
- Бэкенд уже отдает `/v1/public/site-page`; миграция на Next должна сохранить совместимость и кэширование (etag/ISR).
- NodePublicPage — единственный публичный маршрут без SSR. Нужно решить, переносим ли его в Next или оставляем CSR.
- Все публичные страницы завязаны на shared-нормалайзеры (`@caves/site-shared`), это важно для совместного рендера в Next.

## 3. Админка и Site Editor (SPA)

| Раздел / путь | Компонент | Источник данных | Примечания |
|---------------|-----------|-----------------|------------|
| `/site-editor` | `SiteEditorApp` | `/v1/site/pages/*`, `/v1/site/global-blocks/*` | Витрина редактора, использует guarded routes.
| `/site-editor/catalog` | `SitePagesCatalog` | `/v1/site/pages` | Каталог страниц, фильтры/поиск, требует SSR для предпросмотра.
| `/site-editor/page/:id` | `SitePageEditor` | `/v1/site/pages/{id}` + `/v1/public/site-page` (предпросмотр) | Основная форма редактирования.
| `/site-editor/global-blocks` | `SiteGlobalBlocksCatalog` | `/v1/site/global-blocks` | Работа с глобальными блоками (header, footer и т.д.).
| `/site-editor/global-block/:id` | `SiteGlobalBlockEditor` | `/v1/site/global-blocks/{id}` | Поддержка многоязычности в разработке.
| `/dev-tools/schema` | `SchemaPlayground` | локальные JSON-схемы | Вспомогательный раздел для разработчиков.

### Наблюдения
- Все разделы Site Editor используют Vite 7 и общий shared-пакет (`@caves/site-shared`). Это снижает рассинхрон с публичной витриной.
- Предпросмотр страницы тянет `/v1/public/site-page` даже из админки — важно сохранить API стабильным.
- Smoke/e2e для Site Editor пока не автоматизирован (Cypress требует донастройки окружения).

## 4. Shared-слой и API
- `@caves/site-shared` содержит типы, нормалайзеры (`normalizeSitePageResponse`) и вспомогательные компоненты для предпросмотра.
- Контракты: `/v1/public/site-page`, `/v1/site/pages/*`, `/v1/site/global-blocks/*`, `/v1/nodes/*`.
- Для мультиязычности необходимо расширить структуру `meta`, `blocks`, `globalBlocks` (см. ADR 2025-04-28).

## 5. Следующие шаги
1. Завершить smoke/e2e для Site Editor (подготовить Docker/CI раннер для Cypress).
2. Вынести предпросмотр в общий движок (решить: Next preview API или Vite SSR) и задокументировать архитектуру.
3. Подготовить Next-приложение: маршруты, shared-компоненты, интеграция с `/v1/public/site-page`, CI/CD.
4. Описать модель мультиязычности и обновить редактирование/рендеринг блоков.
5. Добавить мониторинг и метрики (latency `/v1/public/site-page`, ошибки SSR, кэш).

## История правок
| Дата | Изменение | Автор |
|------|-----------|-------|
| 30.10.2025 | Обновлена структура документа, приведена к UTF-8, добавлены следующие шаги. | Codex |

