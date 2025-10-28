# Архитектура данных и схема прав для редактора сайта

Документ описывает основные сущности нового редактора публичного сайта, взаимосвязи между ними, изменения в текущих конфигурациях HomeConfig/HomeComposer и роли доступа.

## 1. Сущности

### 1.1 Page

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Уникальный идентификатор страницы |
| `slug` | string (unique) | Публичный путь (`/`, `/dev-blog`, `/help`) |
| `type` | enum (`landing`, `collection`, `article`, `system`) | Категория страницы |
| `status` | enum (`draft`, `published`, `archived`) | Статус опубликованной версии |
| `title` | string | Человекочитаемое имя страницы |
| `locale` | enum (`ru`, `en`, …) | Базовая локаль страницы |
| `owner` | string | Ответственный пользователь/команда |
| `created_at`, `updated_at` | timestamp | Таймстемпы |

### 1.2 PageDraft

Сущность текущего черновика.

| Поле | Тип | Описание |
|------|-----|----------|
| `page_id` | UUID (FK Page) | Ссылка на страницу |
| `version` | integer | Последний номер черновика |
| `data` | JSONB | Конфигурация блоков (аналог `home_config`), структура описана ниже |
| `meta` | JSONB | SEO/OG данные, чек-листы, дополнительные параметры |
| `comment` | string | Примечание к текущему черновику |
| `updated_at` | timestamp | Дата последнего сохранения |
| `updated_by` | string | Пользователь, изменивший черновик |
| `review_status` | enum (`none`, `pending`, `approved`, `rejected`) | Состояние ревью |

### 1.3 PageVersion (история публикаций)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Запись истории |
| `page_id` | UUID | Страница |
| `version` | integer | Порядковый номер публикации |
| `data` | JSONB | Зафиксированная конфигурация блоков |
| `meta` | JSONB | SEO/OG данные |
| `comment` | string | Комментарий к публикации |
| `published_at` | timestamp | Время публикации |
| `published_by` | string | Пользователь |
| `diff` | JSONB | Массив изменений (опционально, хранится после расчёта) |

### 1.4 BlockDefinition (библиотека блоков)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | string | Системный идентификатор шаблона (`hero`, `items_grid`) |
| `title` | string | Название блока |
| `description` | string | Подсказка |
| `schema` | JSON schema | Описание настроек и слотов |
| `data_source` | enum (`none`, `manual`, `auto`, `mixed`) | Поведение источника данных |
| `created_at`, `updated_at` | timestamp | Таймстемпы |

### 1.5 BlockInstance (элемент страницы)

Входит в JSON-конфигурацию страницы:

```json
{
  "id": "hero-1",
  "type": "hero",
  "enabled": true,
  "title": "Hero",
  "slots": { "headline": "...", "cta": { "label": "...", "href": "/" } },
  "layout": { "variant": "full" },
  "dataSource": {
    "mode": "manual",
    "entity": "custom",
    "items": []
  }
}
```

### 1.6 GlobalBlock

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Глобальный блок (header, footer, промо) |
| `key` | string (unique) | Системное имя (`header-default`, `footer-main`) |
| `title` | string | Название |
| `section` | enum (`header`, `footer`, `promo`, ...) | Зона использования |
| `locale` | enum (`ru`, `en`, …) | Базовая локаль (опционально) |
| `status` | enum (`draft`, `published`, `archived`) | Статус опубликованной версии |
| `requires_publisher` | boolean | Требуется ли дополнительное подтверждение (исторически — `site.publisher`, сейчас трактуется как необходимость участия `admin`) |
| `published_version` | integer | Последняя опубликованная версия |
| `draft_version` | integer | Текущий номер черновика |
| `comment` | string | Последний комментарий |
| `updated_at`, `updated_by` | timestamp/string | Метаданные последнего изменения |
| `usage_count` | integer (денорм) | Количество зависимых страниц (обновляется триггером/материализованным view) |

`status` описывает состояние опубликованной версии, даже если черновик находится в работе (`draft_version > published_version`).
`usage_count` хранится для аналитики, но при выборках также пересчитывается подзапросом из `site_global_block_usage`.

### 1.7 GlobalBlockDraft

| Поле | Тип | Описание |
|------|-----|----------|
| `block_id` | UUID (FK GlobalBlock) | Ссылка на блок |
| `version` | integer | Текущий номер черновика |
| `data` | JSONB | Конфигурация блока |
| `meta` | JSONB | Дополнительные параметры (темы, layout) |
| `comment` | string | Примечание к черновику |
| `review_status` | enum (`none`, `pending`, `approved`, `rejected`) | Статус ревью |
| `updated_at`, `updated_by` | timestamp/string | Метаданные |

### 1.8 GlobalBlockVersion

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Запись истории |
| `block_id` | UUID | Ссылка на блок |
| `version` | integer | Порядковый номер публикации |
| `data` | JSONB | Зафиксированная конфигурация |
| `meta` | JSONB | Метаданные версии |
| `comment` | string | Комментарий к публикации |
| `diff` | JSONB | Опциональные изменения по полям |
| `published_at`, `published_by` | timestamp/string | Метаданные публикации |

### 1.9 GlobalBlockUsage

| Поле | Тип | Описание |
|------|-----|----------|
| `block_id` | UUID | Ссылка на глобальный блок |
| `page_id` | UUID | Страница, где используется блок |
| `page_slug` | string | Быстрая ссылка на страницу |
| `page_locale` | string | Локаль страницы |
| `page_status` | enum (`draft`, `published`, `archived`) | Статус опубликованной версии |
| `has_draft` | boolean | Есть ли активный черновик страницы |
| `section` | string | Зона (`header`, `footer`, `sidebar`) |
| `last_published_at` | timestamp | Последняя публикация страницы |

Заполняется сервисом публикации страниц/блоков и используется для предупреждений UI и подтверждения публикации.

### 1.10 AuditLog

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Запись |
| `entity_type` | enum (`page`, `global_block`) | Тип сущности |
| `entity_id` | UUID | Сущность |
| `action` | enum (`create`, `update`, `publish`, `restore`, `review`) | Действие |
| `snapshot` | JSONB | Состояние после действия |
| `actor` | string | Пользователь |
| `created_at` | timestamp | Таймстемп |

## 2. Расширение HomeConfig / HomeComposer

- HomeConfig генерирует/читает JSON для поля `PageDraft.data` и `PageVersion.data`.  
- HomeComposer должен:
  - Уметь получать конфигурацию страницы по `slug`.  
  - Собрать данные из глобальных блоков (header/footer) и встроить в ответ.  
  - Поддерживать разные типы источников данных (manual/auto/custom) аналогично текущей главной.  
  - Учитывать локализацию (locale в `Page` + локализованные слоты).  
  - При публикации глобального блока запускать репаблишинг зависимых страниц и обновление `site_global_block_usage`.
- JSON schema `home_config.schema.json` расширяем новыми типами страниц (например, `faq_list`, `promo_banner`), а также секцией `pageMeta`:

```json
{
  "type": "object",
  "properties": {
    "blocks": { "$ref": "#/definitions/blockList" },
    "meta": {
      "type": "object",
      "properties": {
        "title": { "type": "string", "maxLength": 160 },
        "description": { "type": "string", "maxLength": 320 },
        "ogImage": { "type": "string", "format": "uri" },
        "noindex": { "type": "boolean" }
      }
    }
  }
}
```

## 3. Изменения в БД (черновик миграций)

1. Новые таблицы:  
   - `site_pages` (Page)  
   - `site_page_drafts` (PageDraft)  
   - `site_page_versions` (PageVersion)  
   - `site_global_blocks` (GlobalBlock)  
   - `site_global_block_drafts` (GlobalBlockDraft)  
   - `site_global_block_versions` (GlobalBlockVersion)  
   - `site_global_block_usage` (актуальные зависимости)  
   - `site_audit_log`
2. Миграция текущей главной (`product_home_configs`) в `site_pages` как запись `slug = main`.
3. Индексы: `slug`, `status`, `updated_at` на таблицах страниц и блоков; составные индексы по (`block_id`, `page_id`) и (`page_id`, `block_id`) для `site_global_block_usage`; индекс по `section`/`status` для быстрого фильтра каталога блоков.
4. Триггеры/функции: обновление `usage_count` на `site_global_blocks` при изменении записей `site_global_block_usage`; аудит публикаций записывается в `site_audit_log`.

## 4. Роли и права

| Роль | Возможности |
|------|-------------|
| `user` | Просмотр опубликованных страниц и блоков, без доступа к редактору админки |
| `editor` | Создание и редактирование черновиков страниц и глобальных блоков, публикация в пределах своей области |
| `support` | Просмотр блоков и страниц, комментарии и заметки, помощь командам без изменения структуры |
| `moderator` | Управление ревью, публикация/откат версий, доступ к метрикам и истории |
| `admin` | Управление правами, конфигурацией, системными настройками, критичными операциями |

Дополнительно:
- Для глобальных блоков есть флаг `requires_publisher` — публикацию должен подтвердить пользователь с ролью `admin` (исторический алиас `site.publisher`).
- Все действия фиксируются в `site_audit_log`.

## 5. Тестирование

- Schema-тесты: валидаторы JSON (`home_config.schema.json`) должны принимать конфигурации из `PageDraft.data`.  
- Unit-тесты сервисного слоя: сохранение/получение `Page`, `PageDraft`, `PageVersion`, публикация, восстановление.  
- Интеграционные тесты `HomeComposer`: формирование ответа для страниц разных типов, с учётом глобальных блоков и локалей.  
- Тесты RBAC: проверка методов API на соблюдение ролей.

## 6. Следующие шаги

1. Подготовить реальные миграции SQL по схеме выше и план переноса данных из `product_home_configs`.  
2. Обновить JSON schema и типы TypeScript.  
3. Реализовать API согласно ADR (см. задачу 3).  
4. Настроить default-ролей и миграцию прав.  
5. Подготовить тестовые данные для автотестов и Storybook.

5. Таблица `site_page_metrics` агрегирует показатели страницы за период (`period` = `1d`/`7d`/`30d`) и локаль: просмотры (`views`), уникальные пользователи (`unique_users`), клики по CTA, конверсии, среднее время на странице, долю мобильного трафика, bounce rate, статус актуальности (`status`), задержку источника (`source_lag_ms`). Один ряд соответствует окну [`range_start`, `range_end`].
6. Таблица `site_global_block_metrics` хранит KPI глобальных блоков: показы, клики, конверсии, выручку (опционально), статус источника и список топ-страниц (`top_pages`) для предупреждений при просадке эффективности.


