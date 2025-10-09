# Аудит фронтенда (2025-10-02)

## Кратко
- Основные экраны используют дублируемую логику загрузки и пагинации, что усложняет сопровождение и правки ошибок.
- На страницах по-прежнему смешаны шаблонные классы из дизайна Tailux и новые компоненты из `@ui`, что даёт визуальные и UX-разрывы.
- В кодовой базе осталось много временных заглушек, бэкапов и неиспользуемых представлений, которые вносят шум в структуру проекта.

## Дубликаты кода
- Состояния `page/pageSize/hasNext` и однотипные загрузчики повторяются на нескольких экранах (`setPage`, `setPageSize`, `hasNext`, `load`): `src/pages/content/nodes/NodesPage.tsx:76`, `src/pages/content/quests/QuestsPage.tsx:26`, `src/pages/content/tags/TagsPage.tsx:46`, `src/pages/notifications/BroadcastsPage.tsx:164`.
- Везде для debounce применяется ручной `setTimeout` с одинаковой сигнатурой (`200 мс`), вместо общей утилиты/хука: `src/pages/content/quests/QuestsPage.tsx:90`, `src/pages/content/tags/TagsPage.tsx:120`, `src/pages/content/nodes/NodesPage.tsx:238`, `src/pages/notifications/BroadcastsPage.tsx:243`.
- Константа размеров страницы объявляется заново в каждом модуле (`PAGE_SIZE_OPTIONS`): `src/pages/content/tags/TagsPage.tsx:24`, `src/pages/notifications/BroadcastsPage.tsx:84`, `src/pages/management/Audit.tsx:64`.
- Разметка бейджей статусов/эмбеддингов продублирована в нескольких местах и жёстко завязана на классы шаблона: `src/pages/content/nodes/NodesPage.tsx:124`, `src/pages/content/nodes/components/NodesTable.tsx:99`.
- Во многих экранах ещё лежат `mock`-данные для fallback (например, `src/pages/content/quests/QuestsPage.tsx:18`, `src/pages/content/drafts/DraftsPage.tsx:8`), что дублирует реальный контракт API и скрывает ошибки.

## Устаревшие/несогласованные компоненты
- Блок массовых действий по узлам отдаёт кнопки через старые классы `btn-base btn`, игнорируя `@ui/Button`: `src/pages/content/nodes/components/NodesBulkActions.tsx:27`.
- В `ContentLayout` действия навигации всё ещё собраны на `NavLink` с теми же шаблонными классами, поэтому выглядят иначе, чем кнопки из библиотеки: `src/pages/content/ContentLayout.tsx:56`.
- Страница квестов использует кастомные кнопки и `select` с классами шаблона, вместо унифицированных компонентов: `src/pages/content/quests/QuestsPage.tsx:144`, `src/pages/content/quests/QuestsPage.tsx:196`, `src/pages/content/quests/QuestsPage.tsx:208`.
- Бейджи статусов рендерятся через `span` с классами `badge`, хотя в `@ui` уже есть `Badge`: `src/pages/content/nodes/NodesPage.tsx:127`, `src/pages/content/nodes/components/NodesTable.tsx:99`.

## Несовпадения в стилях и текстах
- На странице квестов и черновиков кириллица испорчена из-за неверной кодировки строк, что рендерится кракозябрами: `src/pages/content/quests/QuestsPage.tsx:18`, `src/pages/content/drafts/DraftsPage.tsx:6`.
- Часть интерфейса по-прежнему англоязычная, даже когда флоу целиком русифицирован (например, заголовки и описания в `ContentLayout`): `src/pages/content/ContentLayout.tsx:52`, `src/pages/content/ContentLayout.tsx:136`.
- На странице тегов отображаются англоязычные пустые состояния и лоадеры, выбивающиеся из остальной локализации: `src/pages/content/tags/TagsPage.tsx:369`, `src/pages/content/tags/TagsPage.tsx:376`.

## Проблемы в верстке и дроверах
- Компонент `Drawer` не объявляет `role="dialog"` и `aria-modal`, зато оставляет невидимую панель в DOM (`pointer-events-none`), из-за чего фокус можно увести за пределы дровера: `src/shared/ui/primitives/Drawer.tsx:14`.
- Внутри `Drawer` отсутствует фокус-ловушка и автоперевод фокуса на заголовок/первый элемент при открытии, поэтому клавиатурная навигация ломается: `src/shared/ui/primitives/Drawer.tsx:21`.
- Закрывающая кнопка дровера представлена символом `×` без иконки/описания, что плохо распознаётся экранными дикторами: `src/shared/ui/primitives/Drawer.tsx:26`.

## Использование alert/prompt/confirm
- Модалки подтверждения и ошибки показаны через браузерные `alert/prompt/confirm`, без унифицированного UI: `src/pages/content/nodes/NodesPage.tsx:377`, `src/pages/content/nodes/NodesPage.tsx:416`, `src/pages/content/nodes/NodesPage.tsx:422`, `src/pages/content/nodes/NodesPage.tsx:432`.
- На странице тегов ошибки удалений/мержей выводятся `alert`, что режет UX и блокирует поток: `src/pages/content/tags/TagsPage.tsx:186`, `src/pages/content/tags/TagsPage.tsx:201`, `src/pages/content/tags/TagsPage.tsx:228`.
- Управление стратегиями связей тоже падает через `alert`, вместо нормальной нотификации: `src/pages/content/relations/RelationsPage.tsx:337`.

## Консольные ворнинги и глушение ошибок
- Ошибки загрузки во многих экранах просто логируются `console.warn` и теряются — пользователь остаётся без обратной связи: `src/pages/content/ContentDashboard.tsx:34`, `src/pages/content/nodes/NodesOverviewPage.tsx:28`, `src/pages/content/tags/TagsPage.tsx:115`.

## Мертвый код и артефакты
- `ContentDashboard` больше не смонтирован (маршрут `/content` редиректит), но файл и все зависимые компоненты `Tops` остались: `src/pages/content/ContentDashboard.tsx:13`, `src/pages/content/Tops/TopTags.tsx:20`, `src/pages/content/Tops/Searches.tsx:20`, `src/pages/content/Tops/Edits.tsx:23`.
- Страница черновиков лежит в боевом каталоге, хотя маршрут переадресует на библиотеку узлов: `src/pages/content/drafts/DraftsPage.tsx:13`, `src/App.tsx:171`.
- В каталоге тегов хранится старый бэкап `TagsPage.tsx.bak`, который не должен попадать в билд: `src/pages/content/tags/TagsPage.tsx.bak:1`.

## Структурные замечания
- Неиспользуемые представления (`DraftsPage`, `ContentDashboard`, `Tops/*`) и бэкап-файлы лучше перенести в архив/`legacy` либо удалить, чтобы не вводить команду в заблуждение.
- Общие хелперы для пагинации, debounce и бейджей стоит вынести в `src/shared` — сейчас каждая страница реализует свою версию и увеличивает стоимость изменений.

## Что делать дальше
1. Выделить общие хуки/утилиты для пагинации и загрузки, заменить прямые `alert/prompt/confirm` на компонентные модалки/тосты.
2. Перевести кнопки и бейджи на компоненты `@ui`, починить текстовые строки (кодировка, локализация) и привести `Drawer` к доступному поведению.
3. Удалить или архивировать мёртвые страницы и бэкап-файлы, чтобы расчистить структуру и предотвратить случайные импорты.
