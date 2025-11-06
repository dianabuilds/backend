# API редактора сайта — кратко

Этот файл фиксирует минимальный набор REST‑эндпоинтов, согласованный с моделью из `overview.md`. Добавляете новое поведение — обновляйте таблицы ниже и OpenAPI.

---

## 1. Общие правила
- **Аутентификация.** Bearer‑токен + CSRF для изменяющих запросов. Роли: `viewer`, `editor`, `publisher`, `admin`.  
- **Формат.** `application/json`, `UTF-8`. Пагинация — `{ "items": [...], "page": 1, "page_size": 20, "total": 120 }`.  
- **Локаль.** Большинство ручек принимает `locale` в query. Если параметр не задан, используется дефолтная локаль сущности.  
- **Ошибки.** `400` (валидация), `401`, `403`, `404`, `409` (конфликт версии/привязок), `422` (бизнес-ограничения).  
- **Версионирование.** Клиент обязан передавать `version` в изменяющих запросах, чтобы избежать lost update.

---

## 2. Блоки (`/v1/site/blocks`)

| Метод | Путь | Роль | Назначение |
|-------|------|------|------------|
| GET | `/blocks` | viewer | Каталог блоков. Фильтры: `scope`, `status`, `is_template`, `section`, `locale`, `q`, `has_draft`, `requires_publisher`, `review_status`, `origin_block_id`, `sort`. |
| GET | `/blocks/{id}` | viewer | Полный блок и список привязок. |
| POST | `/blocks` | editor | Создать блок. Тело: `title`, `scope`, `section`, `is_template?`, `origin_block_id?`, `data`, `meta?`. |
| PATCH | `/blocks/{id}` | editor | Обновить метаданные (`title`, `section`, `is_template`, `origin_block_id`, `meta`). Требует `version`. |
| PUT | `/blocks/{id}/data` | editor | Перезаписать `data` целиком или для указанной `locale`. |
| POST | `/blocks/{id}/publish` | editor/publisher | Зафиксировать черновик, увеличить `version`, записать снапшот в `site_block_versions`. |
| POST | `/blocks/{id}/copy` | editor | Создать копию. Параметры: `scope` (`page` по умолчанию), `is_template`, `title?`. Используется при размещении «рыб» на странице. |
| POST | `/blocks/{id}/preview` | viewer | Возвращает данные блока в нужной `locale` для iFrame. |
| GET | `/blocks/{id}/history` | viewer | Версии блока. |
| POST | `/blocks/{id}/history/{version}/restore` | editor | Перенести данные версии в черновик. |
| POST | `/blocks/{id}/archive` | editor | Пометить блок как `archived`. Ошибка `409`, если есть активные привязки. |

**Формат блока**
```jsonc
{
  "id": "uuid",
  "title": "Hero — default",
  "scope": "shared",
  "is_template": false,
  "origin_block_id": "uuid|null",
  "section": "hero",
  "status": "draft",
  "version": 3,
  "data": {
    "title": {"ru": "Погружайся", "en": "Dive in"},
    "links": [
      {"label": {"ru": "Каталог", "en": "Catalog"}, "href": {"ru": "/ru/catalog", "en": "/en/catalog"}}
    ]
  },
  "meta": {"owners": ["team_public_site"]},
  "updated_at": "2025-12-05T10:00:00Z",
  "updated_by": "editor:irina"
}
```

---

## 3. Страницы (`/v1/site/pages`)

| Метод | Путь | Роль | Назначение |
|-------|------|------|------------|
| GET | `/pages` | viewer | Каталог страниц. Фильтры: `status`, `owner`, `has_draft`, `q`. |
| POST | `/pages` | editor | Создать страницу (`slug`, `title`, `default_locale`, `owner?`). |
| GET | `/pages/{id}` | viewer | Публикация страницы + опубликованные привязки; `locale` в query отфильтровывает блоки. |
| PATCH | `/pages/{id}` | editor | Обновить метаданные (`title`, `slug`, `owner`, `available_locales`). Требует `version`. |
| DELETE | `/pages/{id}` | editor | Пометить как `archived`. |
| GET | `/pages/{id}/draft` | editor | Черновик: метаданные + черновые привязки. |
| PUT | `/pages/{id}/draft` | editor | Сохранить черновик (позиции блоков, комментарий). |
| POST | `/pages/{id}/publish` | editor/publisher | Публикует черновик, фиксирует версии блоков `scope='page'`, создаёт запись в `site_page_versions`. |
| POST | `/pages/{id}/preview` | viewer | Собирает JSON для предпросмотра (учитывает черновые блоки). |
| GET | `/pages/{id}/history` | viewer | Версии страницы. |
| POST | `/pages/{id}/history/{version}/restore` | editor | Перенести версию в черновик. |

**Черновой ответ страницы**
```jsonc
{
  "id": "uuid",
  "title": "Главная",
  "slug": "/",
  "status": "draft",
  "version": 5,
  "available_locales": ["ru","en"],
  "bindings": [
    {
      "binding_id": "uuid",
      "block_id": "uuid",
      "section": "hero",
      "position": 0,
      "locale": null,
      "is_template": false,
      "content_version": 3
    }
  ],
  "comment": "Обновили оффер",
  "updated_at": "2025-12-05T10:15:00Z"
}
```

---

## 4. Привязки блоков (`/v1/site/pages/{id}/blocks`)

| Метод | Путь | Роль | Назначение |
|-------|------|------|------------|
| POST | `/pages/{id}/blocks` | editor | Добавить блок в черновик страницы. Тело: `block_id`, `section`, `position`, `locale?`, `create_copy?`. По умолчанию `create_copy=true`, если исходный блок `is_template`. |
| PATCH | `/pages/{id}/blocks/{binding_id}` | editor | Обновить позицию/локаль. |
| DELETE | `/pages/{id}/blocks/{binding_id}` | editor | Удалить блок из черновика. |
| POST | `/pages/{id}/blocks/{binding_id}/detach` | editor | Отвязать shared-блок → создаёт копию (`scope='page'`) и заменяет привязку. |

---

## 5. Ошибки и соглашения
- `409` — конфликт версии (`version` не совпадает) или попытка архивировать блок с активными привязками.  
- `422` — бизнес-валидация: нет перевода обязательной локали, попытка привязать `is_template=true` блок напрямую к странице, нарушение ограничений секции.  
- Все списки сортируются по `updated_at desc`, если клиент не указал своё `sort`.  
- Любой изменяющий запрос возвращает актуальное состояние сущности, чтобы фронт мог обновить UI без повторных запросов.

---

Это единственная документация по API редактора. Детализация схем находится в `apps/backend/domains/product/site/schemas/` и в `docs/openapi/site-editor.yml`; при расхождении источником истины считается это описание.
