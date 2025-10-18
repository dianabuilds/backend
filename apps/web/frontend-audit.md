# РђСѓРґРёС‚ фронтенда (2025-10-02)

## Кратко
- 2025-10-12: Wave 2 W2-6 — обновлены клиенты nodes/moderation/notifications под новые backend контракты.
- Основные экраны используют дублируемую логику загрузки Рё пагинации, что усложняет сопровождение Рё правки ошибок.
- РќР° страницах РїРѕ-прежнему смешаны шаблонные классы РёР· дизайна Tailux Рё новые компоненты РёР· `@ui`, что даёт визуальные Рё UX-разрывы.
- Р’ РєРѕРґРѕРІРѕР№ базе осталось РјРЅРѕРіРѕ временных заглушек, бэкапов Рё неиспользуемых представлений, которые РІРЅРѕСЃСЏС‚ шум РІ структуру проекта.

## Безопасность
- 2025-10-20: Wave 2 W2-7 — фронтовый клиент читает имена CSRF cookie/header из настроек, кеширует TTL и сбрасывает истёкшие токены.
- Добавлены глобальные уведомления и автоповтор запросов после 429; сценарии проверены Vitest (`csrf.test.ts`, `rate-limit.test.ts`) и Cypress (`security_rate_limit.cy.ts`).

## Дубликаты РєРѕРґР°
- Состояния `page/pageSize/hasNext` Рё однотипные загрузчики повторяются РЅР° нескольких экранах (`setPage`, `setPageSize`, `hasNext`, `load`): `src/pages/content/nodes/NodesPage.tsx:76`, `src/pages/content/quests/QuestsPage.tsx:26`, `src/pages/content/tags/TagsPage.tsx:46`, `src/pages/notifications/BroadcastsPage.tsx:164`.
- Везде для debounce применяется ручной `setTimeout` СЃ одинаковой сигнатурой (`200 РјСЃ`), вместо общей утилиты/С…СѓРєР°: `src/pages/content/quests/QuestsPage.tsx:90`, `src/pages/content/tags/TagsPage.tsx:120`, `src/pages/content/nodes/NodesPage.tsx:238`, `src/pages/notifications/BroadcastsPage.tsx:243`.
- Константа размеров страницы объявляется заново РІ каждом модуле (`PAGE_SIZE_OPTIONS`): `src/pages/content/tags/TagsPage.tsx:24`, `src/pages/notifications/BroadcastsPage.tsx:84`, `src/pages/management/Audit.tsx:64`.
- Разметка бейджей статусов/эмбеддингов продублирована РІ нескольких местах Рё жёстко завязана РЅР° классы шаблона: `src/pages/content/nodes/NodesPage.tsx:124`, `src/pages/content/nodes/components/NodesTable.tsx:99`.
- Р’Рѕ РјРЅРѕРіРёС… экранах ещё лежат `mock`-данные для fallback (например, `src/pages/content/quests/QuestsPage.tsx:18`, `src/pages/content/drafts/DraftsPage.tsx:8`), что дублирует реальный контракт API Рё скрывает ошибки.

## Устаревшие/несогласованные компоненты
- Блок массовых действий РїРѕ узлам отдаёт РєРЅРѕРїРєРё через старые классы `btn-base btn`, РёРіРЅРѕСЂРёСЂСѓСЏ `@ui/Button`: `src/pages/content/nodes/components/NodesBulkActions.tsx:27`.
- Р’ `ContentLayout` действия навигации РІСЃС‘ ещё собраны РЅР° `NavLink` СЃ теми Р¶Рµ шаблонными классами, поэтому выглядят иначе, чем РєРЅРѕРїРєРё РёР· библиотеки: `src/pages/content/ContentLayout.tsx:56`.
- Страница квестов использует кастомные РєРЅРѕРїРєРё Рё `select` СЃ классами шаблона, вместо унифицированных компонентов: `src/pages/content/quests/QuestsPage.tsx:144`, `src/pages/content/quests/QuestsPage.tsx:196`, `src/pages/content/quests/QuestsPage.tsx:208`.
- Бейджи статусов рендерятся через `span` СЃ классами `badge`, хотя РІ `@ui` СѓР¶Рµ есть `Badge`: `src/pages/content/nodes/NodesPage.tsx:127`, `src/pages/content/nodes/components/NodesTable.tsx:99`.

## Несовпадения РІ стилях Рё текстах
- РќР° странице квестов Рё черновиков кириллица испорчена РёР·-Р·Р° неверной РєРѕРґРёСЂРѕРІРєРё строк, что рендерится кракозябрами: `src/pages/content/quests/QuestsPage.tsx:18`, `src/pages/content/drafts/DraftsPage.tsx:6`.
- Часть интерфейса РїРѕ-прежнему англоязычная, даже РєРѕРіРґР° флоу целиком русифицирован (например, заголовки Рё описания РІ `ContentLayout`): `src/pages/content/ContentLayout.tsx:52`, `src/pages/content/ContentLayout.tsx:136`.
- РќР° странице тегов отображаются англоязычные пустые состояния Рё лоадеры, выбивающиеся РёР· остальной локализации: `src/pages/content/tags/TagsPage.tsx:369`, `src/pages/content/tags/TagsPage.tsx:376`.

## Проблемы РІ верстке Рё дроверах
- Компонент `Drawer` РЅРµ объявляет `role="dialog"` Рё `aria-modal`, зато оставляет невидимую панель РІ DOM (`pointer-events-none`), РёР·-Р·Р° чего фокус РјРѕР¶РЅРѕ увести Р·Р° пределы дровера: `src/shared/ui/primitives/Drawer.tsx:14`.
- Внутри `Drawer` отсутствует фокус-ловушка Рё автоперевод фокуса РЅР° заголовок/первый элемент РїСЂРё открытии, поэтому клавиатурная навигация ломается: `src/shared/ui/primitives/Drawer.tsx:21`.
- Закрывающая РєРЅРѕРїРєР° дровера представлена символом `Г—` без РёРєРѕРЅРєРё/описания, что плохо распознаётся экранными дикторами: `src/shared/ui/primitives/Drawer.tsx:26`.

## Использование alert/prompt/confirm
- Модалки подтверждения Рё ошибки показаны через браузерные `alert/prompt/confirm`, без унифицированного UI: `src/pages/content/nodes/NodesPage.tsx:377`, `src/pages/content/nodes/NodesPage.tsx:416`, `src/pages/content/nodes/NodesPage.tsx:422`, `src/pages/content/nodes/NodesPage.tsx:432`.
- РќР° странице тегов ошибки удалений/мержей выводятся `alert`, что режет UX Рё блокирует поток: `src/pages/content/tags/TagsPage.tsx:186`, `src/pages/content/tags/TagsPage.tsx:201`, `src/pages/content/tags/TagsPage.tsx:228`.
- Управление стратегиями связей тоже падает через `alert`, вместо нормальной нотификации: `src/pages/content/relations/RelationsPage.tsx:337`.

## Консольные РІРѕСЂРЅРёРЅРіРё Рё глушение ошибок
- Ошибки загрузки РІРѕ РјРЅРѕРіРёС… экранах просто логируются `console.warn` Рё теряются — пользователь остаётся без обратной СЃРІСЏР·Рё: `src/pages/content/ContentDashboard.tsx:34`, `src/pages/content/nodes/NodesOverviewPage.tsx:28`, `src/pages/content/tags/TagsPage.tsx:115`.

## Мертвый РєРѕРґ Рё артефакты
- `ContentDashboard` больше РЅРµ смонтирован (маршрут `/content` редиректит), РЅРѕ файл Рё РІСЃРµ зависимые компоненты `Tops` остались: `src/pages/content/ContentDashboard.tsx:13`, `src/pages/content/Tops/TopTags.tsx:20`, `src/pages/content/Tops/Searches.tsx:20`, `src/pages/content/Tops/Edits.tsx:23`.
- Страница черновиков лежит РІ боевом каталоге, хотя маршрут переадресует РЅР° библиотеку узлов: `src/pages/content/drafts/DraftsPage.tsx:13`, `src/App.tsx:171`.
- Р’ каталоге тегов хранится старый бэкап `TagsPage.tsx.bak`, который РЅРµ должен попадать РІ билд: `src/pages/content/tags/TagsPage.tsx.bak:1`.

## Структурные замечания
- Неиспользуемые представления (`DraftsPage`, `ContentDashboard`, `Tops/*`) Рё бэкап-файлы лучше перенести РІ архив/`legacy` либо удалить, чтобы РЅРµ вводить команду РІ заблуждение.
- Общие хелперы для пагинации, debounce Рё бейджей стоит вынести РІ `src/shared` — сейчас каждая страница реализует СЃРІРѕСЋ версию Рё увеличивает стоимость изменений.

## Что делать дальше
1. Выделить общие С…СѓРєРё/утилиты для пагинации Рё загрузки, заменить прямые `alert/prompt/confirm` РЅР° компонентные модалки/тосты.
2. Перевести РєРЅРѕРїРєРё Рё бейджи РЅР° компоненты `@ui`, починить текстовые строки (РєРѕРґРёСЂРѕРІРєР°, локализация) Рё привести `Drawer` Рє доступному поведению.
3. Удалить или архивировать мёртвые страницы Рё бэкап-файлы, чтобы расчистить структуру Рё предотвратить случайные импорты.

## Lighthouse-процедура
- РЎР±РѕСЂРєР° + preview: `npm run build && npm run preview -- --port 4173`.
- Мобильный аудит: `npx lighthouse http://localhost:4173/ --preset=mobile --output json --output-path var/lighthouse-home.json`.
- Требуемые метрики: LCP ≤ 2.5 s, CLS ≤ 0.1, TBT ≤ 200 ms, итоговый балл ≥ 85.
- Перед релизом проверяем `/dev-blog` Рё конкретный РїРѕСЃС‚; отчёты прикладываем Рє задаче.`

## Wave 0 — baseline и чек-лист
- Перфоманс мобайл: home 61, dev-blog 73 при цели ≥85 (источники: `var/lighthouse-home.json`, `var/lighthouse-devblog.json`). Проверку ведёт @irina.m, апдейты каждый пятничный sync в #web-platform.
- SEO мобайл: 92 против цели 95; нужны правки мета-тегов и hreflang (`var/lighthouse-home.json`). Ответственный @oleg.s.
- Entry bundle: 0.055 MB (<1.2 MB) после сплиттинга. См. обновлённый `var/frontend-bundle.json` и разнос `vendor-*` чанков.
- Тяжёлые ленивые чанки: vendor-charts-BI2fpLVM.js ≈0.56 MB, vendor-editor-Bd39Bf-k.js ≈0.21 MB (загружаются только после перехода в наблюдение/редактор).
- CLS держится в норме (0.0), но следим за новыми лендингами.

### Wave-1 чек-лист
- [ ] Lazy-load hero изображения и снять повторное измерение Lighthouse.
- [x] Вынести Quill/markdown editor в динамические чанки, пересобрать бандл.
- [ ] Проверить `npm run preview` caching headers и prefetch критических API.
- [ ] Подготовить weekly дашборд с публикацией скоров Lighthouse и размерами чанков.

