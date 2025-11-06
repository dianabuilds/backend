# Общий фронтенд-слой: @caves/site-shared

## Что сделано
- Добавлен пакет `packages/site-shared` (esm, TypeScript) для общих типов и нормализации данных страниц сайта.
- Реализован модуль `site-page` c типами `SitePageResponse`, `SiteGlobalBlock`, `SiteGlobalBlockRef` и утилитой `normalizeSitePageResponse`.
- Настроены алиасы `@site-shared` в `apps/web` (Vite) и `apps/web-next` (Next.js), обновлены `tsconfig` и `webpack/vite` конфигурации.
- Next.js использует общий слой (`normalizeSitePageResponse`) для SSR, placeholder-страниц и SEO-метаданных.
- Vite-проект получил re-export типов (`src/shared/types/sitePage.ts`) — можно плавно мигрировать витрину и редактор на новые контракты.

## Следующие шаги
1. Перевести витрину (`apps/web`) на `/v1/public/site-page`, использовать `normalizeSitePageResponse`.
2. Выделить shared-компоненты UI/форматов блоков, чтобы Next.js и Vite делили один набор шаблонов рендера.
3. Подготовить сборку `@caves/site-shared` (tsc emit d.ts / build) и добавить в CI.
