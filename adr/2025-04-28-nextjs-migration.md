# ADR: Миграция публичной витрины на Next.js

## Дата решения
30.10.2025

## Контекст
- Публичная витрина пока собрана на Vite/SSR и не поддерживает целевой стек (App Router, React Server Components, ISR, маршрутизация `/:slug` через `/v1/public/site-page`). См. [docs/plans/site-editor-publishing-plan.md:86](docs/plans/site-editor-publishing-plan.md:86).
- Граница между Site Editor и публичным фронтом размыта: и админка, и предпросмотр используют собственный SSR и набор зависимостей, что усложняет сопровождение и rollout новых сценариев ([docs/plans/site-editor-publishing-plan.md:94](docs/plans/site-editor-publishing-plan.md:94)).
- Site Editor до недавнего времени работал на Vite < 7 и отдельном SSR на Express — это мешало унифицировать рендер-компоненты и shared-пакет ([docs/plans/site-editor-publishing-plan.md:69](docs/plans/site-editor-publishing-plan.md:69)).
- ADR от 25.10.2025 фиксирует целевую модель, где публичный фронт и Site Editor разделены, но используют общий контракт и shared-слой ([adr/2025-10-25-site-editor.md:11](adr/2025-10-25-site-editor.md:11)).

## Решение
- Публичную витрину переводим на Next.js (App Router, ISR, React 18+). Все маршруты `/:slug` обслуживаются через `/v1/public/site-page`.
- Site Editor остаётся на Vite 7+, но использует общий пакет `@caves/site-shared` и тот же контракт, что публичная витрина. Предпросмотр работает на том же payload и в перспективе переедет на общий рендер.
- План работ фиксируем в виде упорядоченного чек-листа, чтобы команда видела прогресс и понимала, что осталось до запуска в прод.

## Контур внедрения
- **Site Editor**: Vite 7, shared-пакет, контракт `/v1/public/site-page` остаётся общим. Предпросмотр должен использовать тот же рендер-пайплайн, что и публичная витрина (через shared-компоненты или Next preview API).
- **Публичная витрина**: Next.js (App Router, ISR) забирает страницы по `/v1/public/site-page`, кеширует по `ETag`/`Cache-Control` и поддерживает мультиязычность на уровне маршрутов и данных.
- **Shared-слой**: `@caves/site-shared` описывает типы, нормалайзеры, UI-блоки. Любые изменения контракта оформляются через PR с согласованием обеих команд.
- **Мультиязычность**: договориться о структуре `meta`, `blocks`, `globalBlocks`, хранить словари в shared-слое, обновить API и UI (Next + Site Editor).
- **Observability и QA**: автоматизировать smoke/e2e, настроить метрики `/v1/public/site-page`, внедрить rollout-процедуры.

Полный набор задач и критериев готовности описан в [docs/nextjs-migration-task-list.md](../docs/nextjs-migration-task-list.md).

## Последствия
- После выполнения плана публичная витрина работает на Next.js (App Router, ISR), Site Editor — на Vite 7+, а shared-пакет обеспечивает единый контракт и рендер-компоненты.
- Инвестиции в shared-слой, i18n и CI/CD окупятся: релизы станут безопаснее, а технический долг — управляемым.
- Smoke/e2e и мониторинг нужно внедрить до запуска в прод: без них придётся жить в «ручном режиме», что рисково под нагрузкой.
