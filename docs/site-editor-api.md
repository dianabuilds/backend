# API каталога страниц и версий

Документ описывает REST API, доступное фронтенду редактора сайта. Все ответы в формате JSON, авторизация через существующую систему (Bearer + роли `site.*`).

## 1. Страницы

### 1.1 `GET /v1/site/pages`

Возвращает список страниц с фильтрами и пагинацией.

Параметры запроса:
- `page` (number, default 1) — номер страницы
- `page_size` (number, default 20, max 100)
- `type` (string) — фильтр по типу (`landing`, `collection`, `article`, `system`)
- `status` (string) — фильтр по статусу опубликованной версии (`draft`, `published`, `archived`)
- `locale` (string)
- `q` (string) — поиск по заголовку/slug
- `has_draft` (boolean)
- `sort` (string) — `updated_at_desc` (default), `updated_at_asc`, `title_asc`

Права доступа: пользователи без ролей `site.editor`, `site.publisher`, `site.reviewer`, `site.admin` (или глобальных `admin`/`moderator`) получают только опубликованные страницы; черновики доступны им, если страница принадлежит их команде/владению.

Ответ:
```json
{
  "items": [
    {
      "id": "uuid",
      "slug": "/",
      "type": "landing",
      "status": "published",
      "title": "Главная",
      "locale": "ru",
      "owner": "marketing",
      "updated_at": "2025-10-25T09:00:00Z",
      "published_version": 12,
      "draft_version": 15,
      "has_pending_review": true
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 6
}
```

Требуемая роль: `site.viewer` (минимум).

### 1.2 `POST /v1/site/pages`

Создание новой страницы.

Тело запроса:
```json
{
  "slug": "/help",
  "type": "landing",
  "title": "Справка",
  "locale": "ru",
  "owner": "support"
}
```

Ответ: `201 Created` + объект страницы.

Роль: `site.editor`.

### 1.3 `GET /v1/site/pages/{id}`

Детальные данные страницы (без черновика). Возвращает `Page` + статус публикации + ссылки на глобальные блоки.

Роль: `site.viewer`.

### 1.4 `GET /v1/site/pages/{id}/draft`

Получить текущий черновик.

Ответ:
```json
{
  "version": 15,
  "updated_at": "2025-10-25T09:40:00Z",
  "updated_by": "user@caves.dev",
  "review_status": "pending",
  "comment": "готовим релиз",
  "data": { "blocks": [...], "meta": {...} }
}
```

Роль: `site.editor` (владелец/имеющий доступ).

### 1.5 `PUT /v1/site/pages/{id}/draft`

Сохранение черновика.

Тело:
```json
{
  "version": 15,
  "data": { "blocks": [...], "meta": {...} },
  "comment": "обновили hero",
  "review_status": "pending"
}
```

Роль: `site.editor`.

### 1.6 `POST /v1/site/pages/{id}/publish`

Публикация текущего черновика.

Тело:
```json
{
  "comment": "Hero + новый блок рекомендаций"
}
```

Роль: `site.publisher`.

### 1.7 `POST /v1/site/pages/{id}/review`

Изменение статуса ревью (`approved` / `rejected`) + комментарий.

Роль: `site.reviewer`.

### 1.8 `POST /v1/site/pages/{id}/draft/validate`

Серверная проверка конфигурации черновика без сохранения. Возвращает флаг `valid`, нормализованные `data`/`meta` и подробный список ошибок.

Тело запроса (поля опциональны — при их отсутствии используется сохранённый черновик):
```json
{
  "data": { "blocks": [...] },
  "meta": { "title": "..." }
}
```

Успешный ответ:
```json
{
  "valid": true,
  "data": { "blocks": [...] },
  "meta": { "title": "..." }
}
```

Ответ с ошибками:
```json
{
  "valid": false,
  "code": "site_page_validation_failed",
  "errors": {
    "general": [
      { "path": "/blocks", "message": "Идентификаторы блоков должны быть уникальными", "validator": "duplicate" }
    ],
    "blocks": {
      "hero-1": [
        { "path": "/id", "message": "Идентификатор блока должен быть уникальным" }
      ]
    }
  }
}
```

Роль: `site.editor`.

### 1.9 `GET /v1/site/pages/{id}/draft/diff`

Возвращает diff между текущим черновиком и последней опубликованной версией.

```json
{
  "draft_version": 4,
  "published_version": 3,
  "diff": [
    { "type": "block", "blockId": "hero-1", "change": "updated" },
    { "type": "meta", "field": "title", "change": "updated", "before": "Landing", "after": "Landing v2" }
  ]
}
```

Роль: `site.editor`.

### 1.10 `POST /v1/site/pages/{id}/preview`

Генерирует payload для предпросмотра черновика. При отсутствии `data`/`meta` используется сохранённый черновик.

Запрос:
```json
{
  "data": { "blocks": [...] },
  "meta": { "title": "..." },
  "layouts": ["desktop", "mobile"],
  "version": 4
}
```

Ответ:
```json
{
  "page": { "id": "uuid", "slug": "/", "type": "landing", "title": "Главная" },
  "draft_version": 4,
  "published_version": 3,
  "requested_version": 4,
  "version_mismatch": false,
  "layouts": {
    "desktop": { "layout": "desktop", "generated_at": "2025-10-25T12:00:00Z", "data": { ... }, "meta": { ... } },
    "mobile": { "layout": "mobile", "generated_at": "2025-10-25T12:00:00Z", "data": { ... }, "meta": { ... } }
  }
}
```

Роль: `site.editor`.

### 1.11 `GET /v1/site/pages/{id}/metrics`

Возвращает агрегированные KPI страницы за выбранный период.

Параметры запроса:

- `period` — `1d` / `7d` / `30d`, по умолчанию `7d`
- `locale` — целевая локаль (по умолчанию `ru`)

Пример ответа:

```json
{
  "page_id": "uuid",
  "period": "7d",
  "range": { "start": "2025-10-18T00:00:00Z", "end": "2025-10-25T00:00:00Z" },
  "status": "ok",
  "source_lag_ms": 120000,
  "metrics": {
    "views": { "value": 15234, "delta": 0.08 },
    "unique_users": { "value": 9340, "delta": 0.05 },
    "cta_clicks": { "value": 640, "delta": 0.11 },
    "ctr": { "value": 0.042, "delta": 0.03 },
    "conversions": { "value": 210, "delta": 0.04 },
    "conversion_rate": { "value": 0.023, "delta": -0.01 },
    "bounce_rate": { "value": 0.18, "delta": -0.02 },
    "mobile_share": { "value": 0.61, "delta": 0.02 },
    "avg_time_on_page": { "value": 94.2, "delta": 0.07 }
  },
  "alerts": [
    { "code": "views_drop", "message": "Просмотры упали на 12%", "severity": "warning" }
  ]
}
```

Если для выбранного периода данных нет, возвращается объект со статусом `no_data`, пустой картой метрик и списком предупреждений.

Роль: `site.viewer` (или любая роль из `site.*`).

## 2. История версий

### 2.1 `GET /v1/site/pages/{id}/history`

Параметры:
- `limit` (default 10)
- `offset` (default 0)

Ответ:
```json
{
  "items": [
    {
      "version": 12,
      "published_at": "2025-10-20T12:00:00Z",
      "published_by": "user@caves.dev",
      "comment": "Приветственный блок",
      "diff": [{ "blockId": "hero-1", "change": "updated" }]
    }
  ],
  "total": 12
}
```

Роль: `site.viewer`.

### 2.2 `GET /v1/site/pages/{id}/history/{version}`

Возвращает конкретную версию (данные блоков).

Роль: `site.viewer`.

### 2.3 `POST /v1/site/pages/{id}/history/{version}/restore`

Создаёт новый черновик на основе выбранной версии.

Роль: `site.publisher` либо `site.editor` с правом восстановления.

## 3. Глобальные блоки

### 3.1 `GET /v1/site/global-blocks`

Параметры запроса:
- `page` (number, default 1), `page_size` (number, default 20, max 100)
- `section` (`header`, `footer`, `promo`, ...)
- `status` (`draft`, `published`, `archived`)
- `locale` (string)
- `q` (string) — поиск по названию/ключу
- `has_draft` (boolean) — фильтр по наличию черновика (draft_version > published_version)
- `sort` (string) — `updated_at_desc` (default), `updated_at_asc`, `title_asc`, `usage_desc`

Ответ:
```json
{
  "items": [
    {
      "id": "uuid",
      "key": "header-default",
      "title": "Основной хедер",
      "section": "header",
      "locale": "ru",
      "status": "draft",
      "review_status": "pending",
      "requires_publisher": true,
      "published_version": 12,
      "draft_version": 15,
      "usage_count": 5,
      "comment": "обновили CTA",
      "updated_at": "2025-10-26T09:40:00Z",
      "updated_by": "user@caves.dev",
      "has_pending_publish": true
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 6
}
```

Роль: `site.viewer` (минимум). Сортировка по `usage_desc` использует количество связей с `site_global_block_usage`.

### 3.2 `GET /v1/site/global-blocks/{id}`

Возвращает карточку блока, список зависимостей и предупреждения:
```json
{
  "block": {
    "id": "uuid",
    "key": "header-default",
    "title": "Основной хедер",
    "section": "header",
    "locale": "ru",
    "status": "published",
    "review_status": "none",
    "requires_publisher": true,
    "published_version": 12,
    "draft_version": 15,
    "usage_count": 5,
    "comment": "обновили CTA",
    "data": { ... },
    "meta": { ... },
    "updated_at": "2025-10-26T09:40:00Z",
    "updated_by": "user@caves.dev"
  },
  "usage": [
    {
      "page_id": "uuid",
      "slug": "/",
      "title": "Главная",
      "status": "published",
      "locale": "ru",
      "has_draft": true,
      "section": "header",
      "last_published_at": "2025-10-25T17:00:00Z"
    }
  ],
  "warnings": [
    {
      "code": "dependent_page_has_draft",
      "page_id": "uuid",
      "message": "Черновик страницы «Главная» не опубликован"
    }
  ]
}
```

Роли: `site.viewer` (просмотр), `site.editor` (редактирование).

### 3.3 `PUT /v1/site/global-blocks/{id}`

Сохранение черновика глобального блока.

Тело запроса:
```json
{
  "version": 15,
  "data": { "blocks": [...] },
  "meta": { "layout": "header-default", "theme": "dark" },
  "comment": "обновили CTA",
  "review_status": "pending"
}
```

Ответ: `200 OK` + объект блока (ключ `block` из ответа `GET`).

Роль: `site.editor`.

### 3.4 `POST /v1/site/global-blocks/{id}/publish`

Публикация глобального блока. Требует подтверждения влияния на зависимые страницы.

Тело запроса:
```json
{
  "version": 15,
  "comment": "Готовимся к зимней акции",
  "acknowledge_usage": true
}
```

Ответ:
```json
{
  "id": "uuid",
  "published_version": 16,
  "affected_pages": [
    {
      "page_id": "uuid",
      "slug": "/",
      "title": "Главная",
      "status": "published",
      "republish_status": "queued"
    }
  ],
  "jobs": [
    { "job_id": "job-123", "type": "page_republish", "status": "queued" }
  ],
  "audit_id": "audit-uuid",
  "block": { ... },
  "usage": [ ... ]
}
```

Если `acknowledge_usage` не передан и блок используется хотя бы на одной странице — `409 Conflict` c полями `usage` и `usage_count` для отображения предупреждения в UI.

Роль: `site.publisher`.

### 3.5 `GET /v1/site/global-blocks/{id}/history`

Возвращает историю публикаций глобального блока.

Параметры: `limit` (default 10), `offset` (default 0).

Ответ:
```json
{
  "items": [
    {
      "id": "uuid",
      "block_id": "uuid",
      "version": 16,
      "published_at": "2025-10-26T09:45:00Z",
      "published_by": "user@caves.dev",
      "comment": "Готовимся к зимней акции",
      "diff": [{ "field": "cta", "change": "updated" }]
    }
  ],
  "total": 4,
  "limit": 10,
  "offset": 0
}
```

### 3.6 `GET /v1/site/global-blocks/{id}/history/{version}`

Возвращает конкретную опубликованную версию (данные, метаданные, diff).

### 3.7 `POST /v1/site/global-blocks/{id}/history/{version}/restore`

Создаёт новый черновик на основе выбранной версии (номер черновика увеличивается, статус ревью сбрасывается). Возвращает обновлённый блок, зависимости и предупреждения в формате `GET /global-blocks/{id}`.

### 3.8 `GET /v1/site/blocks/{id}/preview`

Возвращает предпросмотр данных для библиотеки блоков (каталог, рекомендации, дев-блог). Используется редактором сайта для отображения карточек.

Параметры:
- `locale` (string, default `ru`) — локаль предпросмотра.
- `limit` (number, default `6`, max `12`) — максимальное количество элементов в выдаче.

Пример ответа:

```json
{
  "block": "recommendations",
  "locale": "ru",
  "source": "live",
  "fetched_at": "2025-10-26T11:10:00Z",
  "items": [
    {
      "id": "42",
      "title": "Персональные подборки",
      "subtitle": "Compass · similarity 0.92",
      "href": "/n/personal-digest",
      "badge": "Compass",
      "provider": "compass",
      "score": 0.92,
      "probability": 0.81
    }
  ],
  "meta": {
    "mode": "site_preview",
    "pool_size": 3,
    "served_from_cache": false
  }
}
```

- `source` может быть `live`, `mock`, `fallback` или `error` — редактор использует это поле, чтобы показать статус данных.
- `items` может быть пустым; в этом случае UI отображает моковые примеры или предупреждение.
- В случае ошибок или отключённых интеграций `meta.reason` содержит текстовую причину (например, `navigation_unavailable`).

Роль: `site.publisher` (при необходимости доступ можно делегировать редакторам).

### 3.9 `GET /v1/site/global-blocks/{id}/metrics`

Возвращает KPI глобального блока и список топ-страниц за выбранный период.

Параметры запроса аналогичны страницам: `period` (`1d`/`7d`/`30d`, default `7d`) и `locale` (default `ru`).

Пример ответа:

```json
{
  "block_id": "uuid",
  "period": "7d",
  "range": { "start": "2025-10-18T00:00:00Z", "end": "2025-10-25T00:00:00Z" },
  "status": "ok",
  "source_lag_ms": 600000,
  "metrics": {
    "impressions": { "value": 40210, "delta": 0.06 },
    "clicks": { "value": 1630, "delta": 0.12 },
    "ctr": { "value": 0.0405, "delta": 0.05 },
    "conversions": { "value": 220, "delta": 0.04 },
    "revenue": { "value": 18450.75, "delta": 0.03 }
  },
  "top_pages": [
    { "page_id": "uuid-1", "slug": "/", "title": "Главная", "impressions": 21000, "clicks": 980, "ctr": 0.0467 },
    { "page_id": "uuid-2", "slug": "/pricing", "title": "Тарифы", "impressions": 9400, "clicks": 420, "ctr": 0.0447 }
  ],
  "alerts": [
    { "code": "block_ctr_drop", "message": "CTR блока упал на 18%", "severity": "warning" }
  ]
}
```

Роль: `site.viewer` (или выше).

## 4. Audit log

`GET /v1/site/audit`

Фильтры: `entity_type`, `entity_id`, `actor`, даты. Используется для дашборда активности.

## 5. Общее

- Все эндпоинты возвращают ошибки в формате:
```json
{ "error": "site_page_not_found", "message": "Страница не найдена" }
```
- Успешные изменения логируются в `site_audit_log`.
- Тесты: unit + интеграционные; OpenAPI спецификация размещается в `docs/openapi/site-editor.yml`.

## 6. TODO

- Реализовать батч-публикацию (`POST /v1/site/publish`) для нескольких страниц (после MVP).  
- Поддержать черновики/версии для локалей (multi-locale) — обсуждается позже.  
- Webhooks/уведомления — описать после внедрения workflow.
