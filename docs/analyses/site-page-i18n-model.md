# Модель i18n для `/v1/public/site-page`

## Цели
- Отдавать страницы публичной витрины на нескольких локалях без дублирования slug/роутов.
- Обеспечить fallback: если запрошенной локали нет, клиент должен понимать, какую локаль вернули.
- Синхронизировать Site Editor, публичный backend и Next.js, чтобы данные/метаданные были единообразны.

## Текущее состояние
- Таблицы `site_pages`, `site_page_drafts`, `site_page_versions` хранят один `data/meta` JSON и строку `locale`.
- `/v1/public/site-page?locale=…` фактически игнорирует локаль (возвращает `locale` страницы или `None`).
- `meta` содержит произвольные поля (например, `title_ru`) без фиксированной схемы; fallback обрабатывается на фронте вручную.
- Глобальные блоки (`global_blocks`) уже имеют поле `locale`, но не поддерживают набор локалей и fallback для связанных страниц.

## Предлагаемая модель хранения
1. **`site_pages`**
   - Добавить колонки: `default_locale` (text, not null, default `ru`), `available_locales` (jsonb array of strings, not null, default `['ru']`).
   - Поле `locale` оставить как alias на `default_locale` (будет убрано после миграций/рефакторинга).
2. **`site_page_drafts` / `site_page_versions`**
   - `data` и `meta` преобразовать в объект вида `{ "locales": { "ru": {...}, "en": {...} }, "shared": {...? } }`.
   - Для обратной совместимости поддерживать плоский формат (single-locale) с автоматической обёрткой при чтении/записи.
3. **Новый столбец** `slug_localized` (jsonb) в `site_pages` для маппинга `locale -> slug` (если slug отличается по локали). Для большинства страниц `slug_localized[default_locale] == slug`.
4. **Глобальные блоки**
   - Добавить `available_locales` (jsonb array) в `site_global_blocks`.
   - Хранить `data/meta` аналогично страницам (`locales` map).

## Контракт `/v1/public/site-page`
Запрос: `GET /v1/public/site-page?slug=/offers&locale=en`.

Ответ (основные поля):
```json
{
  "pageId": "uuid",
  "slug": "/offers",
  "requestedLocale": "en",
  "locale": "en",
  "fallbackLocale": null,
  "defaultLocale": "ru",
  "availableLocales": ["ru", "en"],
  "localizedSlugs": {
    "ru": "/predlozheniya",
    "en": "/offers"
  },
  "meta": { ... },               // данные для выбранной локали
  "metaLocalized": {
    "ru": { ... },
    "en": { ... }
  },
  "payload": { ... },            // локализованный payload/blocks
  "blocks": [ ... ],
  "globalBlocks": {
    "header": {
      "id": "...",
      "availableLocales": ["ru", "en"],
      "locale": "en",
      "fallbackLocale": "ru",
      "data": { ... }
    }
  },
  "globalBlockRefs": [ ... ]
}
```

### Правила fallback
- Если `locale` в запросе отсутствует → используется `default_locale`.
- Если перевод существует и `published_version` > 0 → возвращаем локализованные данные.
- Если перевода нет → `locale` в ответе = `default_locale`, `fallbackLocale = default_locale`, `requestedLocale` = запрошенное значение.
- Клиент может отображать баннер или переключить язык.

### Поля `meta`
- `meta` (локализованный объект) включает `title`, `description`, `keywords`, `og`, `twitter`, `canonical`, `alternates`.
- `metaLocalized` хранит map `locale -> meta`, чтобы Next мог строить `<link rel="alternate">` без дополнительных запросов.
- При fallback в `meta` возвращается содержимое `metaLocalized[fallbackLocale]`.

## Изменения Site Editor API
- Черновик (`GET/PUT /v1/site/pages/{id}/draft`) должен отправлять/принимать структуру с `locales`.
- Валидация (`draft/validate`) проверяет наличие обязательных полей для каждой локали.
- Публикация (`/publish`) публикует только локали, у которых status `ready`. Фронт управляет статусами локалей в черновике.

## Миграции данных
1. Добавить новые колонки `default_locale`, `available_locales`, `slug_localized`.
2. Для существующих страниц:
   - `default_locale = locale`.
   - `available_locales = [locale]`.
   - `slug_localized = { locale: slug }`.
   - Обернуть `draft.meta`, `draft.data`, `version.meta`, `version.data` в `{ "locales": { locale: old_value } }`.
3. Аналогично для глобальных блоков (`available_locales = [locale]`).

## Обновление OpenAPI
- Добавить параметры `locale`, `fallback` (boolean, default true).
- Описать схему `SitePageLocalizedPayload` и включить в ответ.
- Документировать поля `requestedLocale`, `fallbackLocale`, `availableLocales`, `localizedSlugs`, `metaLocalized`.

## Тестирование
- Unit: репозиторий/сервис на выбор локали и fallback.
- Integration: `test_site_public_api.py` сценарии запросов с локалью, отсутствующей локалью, неправильной локалью.
- E2E: smoke проверяет переключение локалей в Next (мета-теги, контент) и Site Editor (предпросмотр + публикация).

## Открытые вопросы
- Какие локали поддерживаем на первом этапе? (ru/en)
- Нужна ли редакторская возможность «черновик локали»: возможно отдельное поле `status` на локалях (draft/published/pending).
- Как синхронизировать slug и sitemap для новых локалей (взаимосвязь с SEO)?
- Требуется ли версионность для локализованных глобальных блоков (скорее да — хранить `published_version` per locale).
