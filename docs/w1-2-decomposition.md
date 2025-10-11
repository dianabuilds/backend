# План декомпозиции задачи W1-2

## Подзадача W1-2.1 — Выделить публичный entry-point
- **Описание**: отделить публичные маршруты (главная, dev-blog) от административной части, чтобы стартовый бандл не подтягивал PrivateAppRoutes и связанные зависимости.
- **Шаги выполнения**:
  1. Создать `src/public/AppPublic.tsx` с маршрутизацией только публичных страниц.
  2. Добавить публичный entry (`src/public-entry.tsx`) без Auth/Toast/Settings провайдеров, настроить SSR-обработчик.
  3. Настроить `vite.config.ts` (`build.rollupOptions.input/manualChunks`) для отдельного public chunk.
  4. Проверить размеры бандлов (`dist/assets/index-*.js`) и убедиться, что публичный бандл < 180 kB gzip.
  5. Прогнать `npm run build && npm run preview` и Lighthouse для `/` и `/dev-blog`.
- **DoR**: определены публичные маршруты, согласован формат SSR без Auth-провайдера.
- **DoD**: public chunk < 180 kB gzip, сборка без предупреждений, Lighthouse performance >= 0.88 после шага 5.
- **AC**:
  - В итоговом отчёте по бандлам `PrivateAppRoutes` отсутствует внутри `index-*.js`.
  - `npm run build` проходит без предупреждения о chunk > 500 kB для публичного `index`.
- **Артефакты**: `src/public/AppPublic.tsx`, `src/public-entry.tsx`, обновлённый `vite.config.ts`, новые lighthouse отчёты.

## Подзадача W1-2.2 — Оптимизировать hero-блок (LCP <= 2.5 s)
- **Описание**: снизить время Largest Contentful Paint за счёт упрощения hero и отдачи критических ресурсов.
- **Шаги выполнения**:
  1. Пересмотреть `HOME_CRITICAL_CSS`: убрать тяжёлые градиенты/тени, переключить шрифт на системный или `font-display: swap`.
  2. Проверить webfont/фоновые ресурсы hero, добавить `preload` только для нужных.
  3. Настроить `sizes`/`fetchpriority` только для LCP-изображения (если оно используется).
  4. Переснять Lighthouse и зафиксировать LCP <= 2.5 s.
- **DoR**: согласована целевая визуализация с продуктом, есть текущее CSS и метрики.
- **DoD**: LCP <= 2500 ms, performance >= 0.88 (при прочих равных).
- **AC**:
  - В отчёте Lighthouse элемент LCP <= 2.5 s, без Render Delay > 1.5 s.
  - Нет штрафов за `Ensure text remains visible during webfont load`.
- **Артефакты**: обновлённый `HomePage.tsx` (CSS/markup), новый lighthouse отчёт.

## Подзадача W1-2.3 — Скорректировать `prefetch.ts`
- **Описание**: снизить накладные запросы и long tasks из-за агрессивного prefetch.
- **Шаги выполнения**:
  1. Добавить проверку `document.visibilityState === 'hidden'` и early return.
  2. Отключить prefetch для путей `/v1/public/home` при аудите или добавить конфигурацию.
  3. Сократить TTL и не использовать `prefetched` карту для одноразовых страниц.
  4. Покрыть helper unit-тестами (например, `usePrefetchLink`) для saveData/effectiveType.
- **DoR**: понятно, какие пути надо исключить, есть текущая реализация helper.
- **DoD**: Lighthouse не показывает 500-х из prefetch и TBT < 200 ms.
- **AC**:
  - В waterfall нет сетевых ошибок `v1/public/home` во время аудита.
  - `long-tasks` < 200 ms суммарно из `index-*.js` (доминирующий chunk).
- **Артефакты**: обновлённые `prefetch.ts`, тесты, свежий lighthouse отчёт.

## Подзадача W1-2.4 — Переработать загрузку блоков Home
- **Описание**: обеспечить плавный рендер блоков без повторного появления skeleton и без откладывания LCP.
- **Шаги выполнения**:
  1. Вынести тяжёлые блоки (`BlockRenderer`/виджеты) в ленивые компоненты внутри самого блока, а не вокруг всего списка.
  2. Удалить `useDeferredBlocks` или ограничить его использованием для второстепенных частей.
  3. Обновить fallback на лёгкую, но статичную версию (без `animate-pulse`).
  4. Протестировать сценарии `loading`, `error`, `data`, убедиться что не конфликтуют с SSR.
  5. Снять метрики (LCP/TBT) после оптимизации.
- **DoR**: известны тяжёлые компоненты, есть доступ к `BlockRenderer`.
- **DoD**: нет `long-tasks` > 250 ms от `HomeBlocks`, LCP держится <= 2.4 s.
- **AC**:
  - При `loading && !data` показывается статичный fallback.
  - Suspense используется локально внутри тяжёлых блоков, а не вокруг всей страницы.
- **Артефакты**: обновлённые `HomePage.tsx`, `BlockRenderer.tsx`, lighthouse отчёт.

## Подзадача W1-2.5 — Финальная интеграция и документация
- **Описание**: собрать результаты, проверить DoD и синхронизировать документацию.
- **Шаги выполнения**:
  1. Запустить `npm run build`, `npm run preview`, Lighthouse для `/` и `/dev-blog`.
  2. Зафиксировать JSON-отчёты в `var/lighthouse-home.json`, `var/lighthouse-devblog.json`.
  3. Обновить `apps/web/frontend-audit.md` (описание оптимизаций + дата).
  4. Подготовить summary для #web-platform.
- **DoR**: все предыдущие подзадачи закрыты, есть актуальные бандлы.
- **DoD**: Performance >= 0.85 и SEO >= 0.95 на обеих страницах, LCP <= 2.5 s.
- **AC**:
  - JSON отчёты в `var/` обновлены и закоммичены.
  - В `frontend-audit.md` добавлен раздел с описанием изменений.
  - Готов краткий текст/сводка для Slack.
- **Артефакты**: обновлённые файлы в `var/`, `apps/web/frontend-audit.md`.
