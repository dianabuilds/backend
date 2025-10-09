# ADR 2026-10-07 Frontend Refactor

## Статус
Accepted

## Контекст
Админский фронтенд (apps/web/src) заметно вырос и унаследовал крупные монолитные файлы, дублированные вспомогательные функции и смешение UI-слоёв с бизнес-логикой. Это снижает скорость разработки, усложняет добавление фич и поддержку тестов. Цель ADR — зафиксировать полный перечень шагов рефакторинга и критериев приёмки, чтобы привести кодовую базу к модульной архитектуре и облегчить дальнейшее развитие.

## Проблема
- Страницы Notifications, Management, Relations, Moderation содержат 500+ строк каждая и одновременно решают задачи UI, бизнес-логики и работы с API.
- Общие хелперы (форматирование дат, чисел) дублируются в десятках файлов, а shared/utils/format.ts содержит поломанную кодировку.
- shared/api/client.ts превратился в "god-object", объединяя управление куки, CSRF, fetch и загрузки; shared/api/auth.ts зависит от несуществующего apiFetch.
- Лэйауты (App.tsx, Topbar.tsx, Sidebar.tsx) содержат избыточный код, хардкодят навигацию и повторяемые конструкции.
- Плохая читаемость (например, тысячи пустых строк в ModeratorPanel.tsx) мешает ревью и поддержке.

## Решение
Выполнить структурный рефакторинг фронтенда по направлениям:
1. Разделение монолитных страниц на feature-модули.
2. Введение общего слоя API и хуков данных.
3. Консолидация и исправление утилит форматирования.
4. Рационализация лэйаутов и навигации.
5. Нормализация кодовой базы (форматирование, тесты, документация).

## План действий и критерии приёмки
### 1. Разделение Notifications
**Действия**
- Создать директорию pages/notifications/modules (или features/notifications) с подпапками broadcasts, templates, channels, history.
- Для каждой страницы выделить презентационный компонент, хук данных useNotifications*Query, модуль API (shared/api/notifications.ts) и компоненты форм.
- Обновить страницы так, чтобы они только собирали подмодули.
- Добавить unit-тесты на новые хуки (React Testing Library + MSW).

**Прогресс (2026-10-07)**
- [x] Broadcasts вынесены в apps/web/src/features/notifications/broadcasts, страница apps/web/src/pages/notifications/BroadcastsPage.tsx подключает модуль через ContentLayout.
- [x] Settings вынесены в apps/web/src/features/notifications/settings, общий слой shared/api/notifications.ts и тесты обновлены под новые операции предпочтений.
- [x] Templates подключены через useNotificationTemplates, компонент TemplatesView очищен от прямых API-вызовов, добавлен unit-тест hooks.test.tsx.
- [x] Общий слой useNotificationsQuery покрывает channels/history/templates с единым управлением загрузкой и ошибками; обновлены хуки и тесты.
- [x] Broadcasts/ Templates переведены на useNotificationBroadcasts + useNotificationBroadcastActions/useNotificationTemplatesManager; добавлены unit-тесты hooks (broadcasts/templates).

- [x] Management: shared/api разбит на management/{billing,flags,integrations,system}, UI страницы (FlagsView, IntegrationsView, SystemView) работают через typed API и общие типы PlatformAdmin*; PlatformAdminFrame экспортирует типы из shared.
- [x] Channels/History: shared/api разбит на notifications/{channels,history,preferences,...} с нормализованными ответами; хуки перенесены в features/notifications/common/hooks, страницы каналов/истории стали thin-wrapper; unit-тесты обновлены (npm run test -- shared/api/notifications.test.ts features/notifications/channels/hooks.test.tsx features/notifications/history/hooks.test.tsx).

**QA 2026-10-08 (Notifications)**
- [x] Unit: npm run test -- shared/api/notifications.test.ts features/notifications/channels/hooks.test.tsx features/notifications/history/hooks.test.tsx (PASS).
- [x] Unit: npm run test -- src/features/notifications/templates/hooks.test.tsx src/features/notifications/broadcasts/hooks.test.tsx (PASS).
- [ ] Smoke: dev-сборка notifications (каналы, история, оповещения) — запланировано после интеграции Management блоков.

**QA 2026-10-08 (Management)**
- [x] Unit: npm run test -- shared/api/management.test.ts (PASS, покрыт management/ai).
- [ ] Smoke: пройти сценарии Flags/Integrations/System и Management AI на dev после миграции остатка Management.
  - Запланировать отдельное окно на dev, подготовить seed данных для моделей/провайдеров и fallback-правил.
  - Проверить загрузку метрик (главная панель, UsageSection), изменение статусных табов и ручное обновление.
  - Протестировать CRUD: создание/редактирование/отключение модели, провайдера и fallback-правила, откат изменений.
  - Убедиться, что playground выполняет запросы, отображает латентность и корректно обрабатывает ошибки.

Следующие шаги 2026-10-08 (Management & Shared)
- [x] Payments: вынесены запросы/мутации в useManagementPayments, страница использует typed managementApi и тонкий хук данных.
- [x] Tariffs: создан useManagementTariffs, страница переведена на typed billing plans API и централизованные действия.
- [x] Audit: вынесен useManagementAudit с typed managementApi, страница apps/web/src/pages/management/Audit.tsx стала thin-wrapper.
- [x] AI: ManagementAI переведён на useManagementAi с typed managementApi; остался smoke-план.



- Ни один файл в pages/* не превышает 300 непустых строк.
- Хуки данных переиспользуются минимум в двух компонентах там, где это оправдано.
- Форматтеры и обработчики не дублируются между страницами.
- Тесты обновлены, добавлены smoke-тесты на ключевые сценарии.
- Snapshot или визуальные тесты (если есть) актуализированы.

### 3. Реорганизация shared/api
**Действия**
- Разбить shared/api/client.ts на client/base.ts, client/csrf.ts, client/uploads.ts, client/auth.ts.
- Настроить shared/api/index.ts как публичный фасад.
- Обновить импорты в кодовой базе.
- Переписать shared/api/auth.ts на новый клиент или удалить при дублировании.
- Добавить Jest-тесты на заголовки, обработку 401 и кэширование CSRF.

- shared/api/client.ts <= 200 строк, остальные модули <= 150.
- Нет обращений к устаревшему apiFetch.
- AuthProvider компилируется и проходит тесты.
- Обновлены мок-объекты в тестах.

**Прогресс (2026-10-08)**
- [x] Клиент разбит на `apps/web/src/shared/api/client/{base,csrf,auth,uploads}.ts` и фасад `client/index.ts`.
- [x] Добавлены namespace-модули `shared/api/{management,nodes,relations,observability,moderation,notifications}` с единым входом `shared/api/index.ts`.
- [x] `shared/api/auth.ts` переписан на `apiFetch`, прямых вызовов устаревшего клиента не осталось.
- [x] Выделены витест-наборы для management/nodes/relations/observability/notifications (см. `apps/web/src/shared/api/*.test.ts`).
- [x] Добавлен модуль `shared/api/management/ai.ts` с CRUD для моделей/провайдеров/fallback/playground.

**QA 2026-10-08 (shared/api)**
- [x] Unit: npm run test -- shared/api/management.test.ts (PASS, покрыт management/ai).

**Следующие шаги**
- [ ] Допокрыть клиент негативными сценариями (timeouts/uploads) и `notifyAuthLost`.
- [ ] Прогнать интеграционные тесты после миграции AI/Navigation.

### 4. Исправление и консолидация форматтеров
**Действия**
- Исправить shared/utils/format.ts, заменив искажённые строки на корректные.
- Добавить функции formatDate, formatDateTime, formatRelativeTime, formatNumber, formatPercent, formatCurrency, formatLatency, formatTimestamp.
- Дополнить JSDoc и типы настроек.
- Заменить локальные функции в Topbar, Notifications, Management, Observability, Moderation.
- Добавить unit-тесты на форматирование.

- rg "function format" pages возвращает только ссылки на общий модуль.
- Тесты покрывают граничные случаи (невалидные даты, null, локаль).
- TypeScript проходит без предупреждений.

**Прогресс (2026-10-08)**
- [x] `shared/utils/format.ts` переписан, добавлены функции formatDateTime/Number/Percent/Bytes/Duration с fallback-логикой.
- [x] Добавлен Vitest-набор `apps/web/src/shared/utils/format.test.ts` с граничными сценариями.
- [x] Notifications/Management/Moderation страницы переведены на общий модуль форматирования (`apps/web/src/features/notifications/**`, `apps/web/src/pages/moderation/**`).
- [ ] Topbar и analytics-панели ещё используют локальные хелперы.

**QA 2026-10-08 (format)**
- [x] Unit: npm run test -- shared/utils/format.test.ts (PASS).

**Следующие шаги**
- [ ] Мигрировать Topbar/AnalyticsPanel на shared/utils/format и удалить дубли.

### 5. Навигация и лэйауты
**Действия**
- Создать shared/navigation/routes.ts с описанием маршрутов, ролей и layout.
- Переписать App.tsx на генерацию Routes из конфига.
- Использовать конфиг в Sidebar и Topbar.
- Вынести из Topbar хук useInbox и компонент UserMenu.
- Прогнать форматирование (Prettier, ESLint).

- App.tsx <= 150 строк, Sidebar.tsx <= 200, Topbar.tsx <= 250.
- Есть unit-тест на генерацию роутов и guard.
- Sidebar и Topbar полагаются только на конфигурацию.
- Smoke или e2e тест подтверждает отсутствие регрессий.

**Прогресс (2026-10-08)**
- [ ] Конфиг маршрутов ещё не вынесен: App.tsx, Sidebar.tsx, Topbar.tsx продолжают держать логику и прямые импорты API.
- [ ] Topbar по-прежнему тянет inbox через fetchNotificationsHistory и форматирует даты локально.

**Следующие шаги**
- [ ] Сформировать `shared/navigation/routes.ts`, переписать App/Sidebar/Topbar на генерацию из конфига.
- [ ] Вынести меню пользователя и инбокс в отдельные хуки после миграции навигации.

### 6. Нормализация admin nodes components
**Действия**
- Удалить лишние пустые строки, применить Prettier.
- Разделить крупные панели на меньшие компоненты и вынести общие части в pages/admin/nodes/shared.

- Каждый файл <= 400 физических строк, непустых <= 250.
- Появилось минимум три переиспользуемых компонента в shared.
- Линтер и тайпчек проходят.

**Прогресс (2026-10-08)**
- [x] Nodes: список и таблица вынесены в feature-модуль apps/web/src/features/content/nodes, страницы стали thin-wrapper.
- [x] Relations: стратегии/preview вынесены в feature-модуль apps/web/src/features/content/relations с typed API и thin-wrapper.
- [x] Observability: страницы и API вынесены в features/observability с typed shared api и thin-wrapper.

**QA 2026-10-08 (Nodes)**
- [x] Unit: npm run test -- shared/api/nodes.test.ts (PASS).
- [ ] Smoke: пройти nodes поток (фильтры, bulk actions) на dev после переноса Relations/Observability.

**QA 2026-10-08 (Relations)**
- [x] Unit: npm run test -- shared/api/relations.test.ts (PASS).
- [ ] Smoke: пройти стратегические сценарии (refresh, save weight, preview) на dev.

**QA 2026-10-08 (Observability)**
- [x] Unit: npm run test -- shared/api/observability.test.ts (PASS).
- [ ] Smoke: проверить панели Observability (overview/api/llm/rum) на dev.

### 7. Тесты и документация
**Действия**
- Обновить README в apps/web с описанием новой структуры.
- Добавить диаграмму модулей в docs/frontend-audit.md или аналог.
- Пересмотреть конфиги Qodana, ESLint, Prettier.
- Запустить полный набор тестов и зафиксировать результат.

- README описывает структуру и гайд по добавлению фич.
- CI полностью зелёный.
- Документированы изменения конфигураций.

**Прогресс (2026-10-08)**
- [x] apps/web/README.md обновлён: структура модулей, UI primitives, Storybook/Chromatic сценарии.
- [x] docs/admin-ui-interaction-rules.md фиксирует правила быстрых действий, метрик и адаптивности для админских экранов.
- [x] Добавлены vitest config и общий setup (`apps/web/vitest.config.ts`, `apps/web/src/test/setup.ts`), скрипты npm синхронизированы.
- [ ] Диаграмма модулей и конфиги Qodana/ESLint ещё не обновлены.

**QA 2026-10-08 (test run)**
- [x] Targeted unit: npm run test -- shared/api/{management,nodes,relations,observability}.test.ts (PASS).
- [x] Targeted unit: npm run test -- shared/utils/format.test.ts (PASS).
- [ ] Полный npm run test + lint/typecheck запустить после стабилизации AI/navigation.

### 8. Унификация таблиц
**Действия**
- Провести инвентаризацию всех таблиц во фронтенде: зафиксировать используемый компонент (общий @ui/table или ручная разметка), наличие быстрых действий, сортировки, зебры, sticky-хедера.
- Совместно с продуктом и дизайном согласовать набор пресетов таблиц (base, management, surface) и сценарии их применения.
- Расширить shared/ui/table пропами preset, actions, headerSticky, zebra, hover, а также добавить вспомогательные компоненты TableEmpty, TableLoading, TableError, Table.Actions.
- Описать пресеты в Storybook/документации, обеспечить единые токены цветов, отступов и состояний.
- Мигрировать все страницы на новый API таблиц, заменить кастомные <table> (Nodes, AI Rules, Models и др.) на использование @ui/table.
- Убедиться, что TablePagination присутствует под каждой таблицей и работает единообразно.

- Все таблицы построены на shared/ui/table с явным preset; ручные <table> остаются только там, где документировано исключение.
- Быстрые действия выводятся inline (actions="inline") там, где это требование UX, и снабжены aria-label/Tooltip.
- Общие состояния (пусто, ошибка, загрузка) отображаются через TableEmpty/TableLoading/TableError.
- Storybook/документация содержит примеры всех пресетов; дизайнеры и QA подтверждают визуальную консистентность.
- Smoke- или визуальные тесты покрывают ключевые таблицы (Nodes, Notifications, Moderation Users, AI Models).

**Прогресс (2026-10-08)**
- [x] `apps/web/src/shared/ui/table/index.tsx` расширен пресетами base/management/surface, добавлены Table.Empty/Table.Error/Table.Loading/Table.Actions.
- [x] Storybook: `apps/web/src/shared/ui/table/Table.stories.tsx` описывает пресеты, пагинацию и состояния.
- [x] Notifications и Management (Payments/Tariffs/Flags) используют `Table.Table` и стандартные состояния.
- [ ] Nodes/Moderation/AI пока держат кастомные `<table>`; требуется миграция.

**Следующие шаги**
- [ ] Переехать с `<table>` в features/content/nodes и management/ai на @ui/Table + вынести нестандартные ячейки в Table.Slot.
- [ ] Добавить визуальные снапшоты (Chromatic) для новых пресетов до smoke-плана.

### 9. Унификация hero-блоков
**Действия**
- Провести аудит страниц с крупными hero-заголовками (PageHeader, кастомные блоки в ContentLayout, Observability, Management, Notifications) и классифицировать сценарии: обзор/дашборд, инструментальная страница, второстепенный список.
- Определить правила применения hero: использовать только на обзорных страницах или там, где нужны краткие метрики/первичные CTA; для узкоспециализированных списков и форм применять компактный заголовок.
- Расширить @ui/PageHeader (или создать PageHero) пропами variant (default, metrics, compact), metrics, primaryActions, secondaryActions, tabs, onCollapse, ограничив высоту блока (max 280–320px на десктопе).
- Стандартизировать вывод метрик: не более пяти, через компактную версию MetricCard (или новый HeroMetric), допускается дополнительная ссылка/tooltip; при отсутствии данных показывать placeholder или скрывать секцию.
- Зафиксировать поведение контролов: primary CTA слева, вторичные действия/фильтры — справа или в нижнем ряду; предусмотреть опцию inlineFilters для компактного отображения.
- Реализовать responsive-поведение: на ширине < 1280px метрики переходят в 2/1 колонки, текст и описания сокращаются; добавить режим collapsed для таблиц, где нужен дополнительный вертикальный простор.
- Обновить шаблоны страниц (ContentLayout, ObservabilityLayout, ManagementLayout и др.), чтобы они использовали новые варианты hero, и убрать локальные стили.
- Документировать пресеты hero-блоков в Storybook/MDX + добавить рекомендации по тестированию (визуальные снапшоты).

- Каждая страница явно выбирает вариант hero (default/metrics/compact) или полностью отказывается от него; причины отказа документированы.
- Высота hero-блоков на десктопе не превышает 320px, на планшете — 360px; на мобильном контент складывается в одну колонку без горизонтального скролла.
- Метрики выводятся через стандартный компонент, количество не превышает трёх; при отсутствии данных секция скрывается или показывает унифицированный placeholder.
- Контролы (primary/secondary) соответствуют гайдлайнам: primary CTA всегда доступна без скролла, второстепенные действия не «уползают» за пределы hero.
- Обновлённый PageHeader/PageHero покрыт Storybook-примером и визуальными тестами; QA подтверждает консистентность между разделами.
- Обзорные страницы (например, Nodes Overview, Observability Overview, Management Overview) остаются визуально насыщенными, при этом основное рабочее содержимое попадает в первый экран на стандартном ноутбуке (1440x900).

**Прогресс (2026-10-08)**
- [x] `apps/web/src/shared/ui/patterns/PageHero.tsx` реализует варианты default/metrics/compact, breadcrumbs и сетку метрик.
- [x] Storybook и MDX (`apps/web/src/shared/ui/patterns/PageHero.stories.tsx`, `PageHero.docs.mdx`) описывают сценарии и ограничения.
- [x] docs/admin-ui-interaction-rules.md фиксирует требования к hero/метрикам/быстрым действиям.
- [ ] Страницы Management/Observability/Moderation пока используют PageHeader; интеграция с PageHero не начата.
- [ ] Не подготовлены smoke/visual сценарии под новый hero.

**Следующие шаги**
- [ ] Запланировать миграцию hero по доменам (Management, Observability, Notifications, Moderation) и обновить сторибуки после внедрения.
- [ ] Переписать ContentLayout/ManagementLayout на PageHero, синхронизировать QA чеклисты и визуальные снапшоты.

## Дорожная карта реализации
1. **Подготовка и заморозка контекста**
   - Подтвердить объём работ с командами и владельцами доменов, согласовать временное окно разработки и возможный freeze на новые фичи.
   - Зафиксировать baseline метрик (время загрузки ключевых страниц, lighthouse/rum, покрытие тестами) и собрать отчёт QA о текущих проблемах.
   - Обновить ADR статус до Accepted после утверждения плана, назначить ответственных по направлениям (API, UI, страницы).

2. **UX/дизайн-консолидация**
   - Выполнить аудит таблиц и hero-блоков, согласовать пресеты с дизайном/продуктом, подготовить Figma-референсы и правила использования.
   - Зафиксировать требования к быстрым действиям, метрикам, адаптивности и поведению контролов.
   - Согласовать план коммуникации с QA/поддержкой и перечень материалов, которые нужно обновить (гайдлайны, скриншоты, тренинги).

3. **Инфраструктурные изменения**
   - Разбить shared/api, обновить shared/utils/format, внедрить новые Table/PageHero компоненты, подготовить Storybook/MDX и юнит-тесты.
   - Настроить визуальные тесты/скриншоты для ключевых UI-паттернов; обновить конфиги lint/prettier при необходимости.
   - Обновить документацию для разработчиков (README, CONTRIBUTING) по новым примитивам.

4. **Функциональный рефакторинг страниц**
   - Параллельно по доменам вынести бизнес-логику в feature-модули (Notifications, Management, Relations, Moderation, Nodes).
   - Стабилизировать хуки данных, API и типы перед массовой миграцией UI.
   - Обеспечить обратную совместимость контрактов, чтобы тесты и смежные сервисы не ломались в процессе.

5. **UI-миграции**
   - Перевести таблицы на пресеты @ui/table, удалить кастомные <table> и старые стили.
   - Обновить hero-блоки/PageHeader для обзорных страниц, внедрить вариант compact для рабочих списков.
   - Проверить responsive, empty/error states, доступность (aria-label, tabindex) после каждого шага.

6. **Интеграционное тестирование и QA**
   - Прогнать unit, smoke, e2e (если есть), визуальные тесты; собрать отчёты и зафиксировать изменения метрик производительности.
   - Совместно с QA выполнить регрессию основных сценариев (Nodes, Notifications, Moderation, Management, Observability).
   - Обновить аналитические трекинги и убедиться, что события не сменили названия/структуры.

7. **Релиз и завершение**
   - Подготовить changelog, обновить пользовательскую документацию и материалы поддержки.
   - Провести демо для стейкхолдеров, собрать фидбек, зафиксировать lessons learned в ретро.
   - Снять freeze, зачистить временные фичи-флаги, закрыть тикеты и обновить ADR статус (если нужны изменения по итогам).
## Определение завершения ADR
- Все пункты плана выполнены, изменения смержены.
- Создан changelog с секцией "Frontend Refactor 2026-10".
- Итоги зафиксированы в ретро-заметке (Notion или Confluence).
- QA и продукт подписали приёмку (скриншоты или демо).
- Удалены временные файлы и устаревшие типы.

## Риски и смягчение
- Регресс из-за объёма изменений: обязательные smoke и e2e тесты, feature flags.
- Конфликты с параллельными задачами: объявить freeze и разбить работу на несколько PR.
- Зависимость от тестовой среды: заранее забронировать окно и ответственных.

## Последствия
- Положительные: модульность, меньше дублирования, проще онбординг.
- Отрицательные: временное замедление разработки, необходимость обучения, риск merge-конфликтов.

## Связанные материалы
- apps/web/frontend-audit.md
- ARCHITECTURE.md
- Отчёты Qodana и ESLint
































































