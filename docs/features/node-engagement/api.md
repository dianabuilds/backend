# Админское API Node Engagement

Документ описывает основные маршруты и требования к админским эндпоинтам Node Engagement. Используется при разработке, ревью и тестировании интерфейсов модерации.

## Аутентификация

- Требуются сессионные cookies и заголовок `X-CSRF-Token`.
- Админские ручки дополнительно проверяют заголовок `X-Admin-Key`.
- Формат данных — `application/json`.

## Просмотры (Views)

### `POST /v1/nodes/{id}/views`
Регистрирует просмотры ноды.

Тело запроса:
```json
{
  "amount": 1,
  "fingerprint": "device-hash",
  "at": "2025-10-02T12:00:00Z"
}
```

Ответ:
```json
{
  "id": 123,
  "views_count": 15
}
```

### `GET /v1/nodes/{id}/views`
Возвращает суммарные значения и помесячные/подневные срезы.

Параметры запроса: `limit` (1–90), `offset` (>=0).

Ответ:
```json
{
  "id": 123,
  "total": 15,
  "buckets": [
    {"node_id": 123, "bucket_date": "2025-10-01", "views": 10},
    {"node_id": 123, "bucket_date": "2025-09-30", "views": 5}
  ]
}
```

## Реакции

- `POST /v1/nodes/{id}/reactions/like` — ставит лайк от текущего пользователя и возвращает сводку.
- `DELETE /v1/nodes/{id}/reactions/like` — снимает лайк.
- `GET /v1/nodes/{id}/reactions` — возвращает суммарные значения и реакцию текущего пользователя (если авторизован).

## Комментарии

### `GET /v1/nodes/{id}/comments`
Параметры: `parentId`, `limit` (<=200), `offset`, `includeDeleted` (только автор ноды или модератор).

Каждый элемент содержит `id`, `node_id`, `author_id`, `parent_comment_id`, `depth`, `content`, `status`, `metadata`, `created_at`, `updated_at`.

### `POST /v1/nodes/{id}/comments`
Тело:
```json
{
  "content": "string",
  "parent_id": null,
  "metadata": {}
}
```

### `DELETE /v1/nodes/comments/{comment_id}`
Параметры: `hard`, `reason`. Доступно автору комментария, автору ноды или модератору.

### `PATCH /v1/nodes/comments/{comment_id}/status`
Тело: `{ "status": "hidden", "reason": "spam" }`. Только модератор.

### Управление блокировками
- `POST /v1/nodes/{id}/comments/lock` — `{ "locked": true, "reason": "maintenance" }`. Автор ноды или модератор.
- `POST /v1/nodes/{id}/comments/disable` — `{ "disabled": true, "reason": "freeze" }`. Автор ноды или модератор.
- `POST /v1/nodes/{id}/comments/ban` — `{ "target_user_id": "uuid", "reason": "abuse" }`.
- `DELETE /v1/nodes/{id}/comments/ban/{user_id}` — снимает локальный бан.
- `GET /v1/nodes/{id}/comments/bans` — список активных банов (`node_id`, `target_user_id`, `set_by`, `reason`, `created_at`).

## Поля карточки ноды

`GET /v1/nodes/{id}` возвращает `views_count`, `reactions_like_count`, `comments_disabled`, `comments_locked_by`, `comments_locked_at` — эти поля используются в админской карточке.

## Коды ошибок

- `400`: `amount_invalid`, `fingerprint_invalid`, `timestamp_invalid`, `content_required`, `parent_id_invalid`, `metadata_invalid`, `target_user_id_required`.
- `401`: `unauthorized`.
- `403`: `forbidden`, `insufficient_role`.

## Тесты и отладка

- Е2Е сценарии: `apps/backend/app/tests/test_nodes_api.py::test_node_engagement_endpoints`.
- Локальный запуск: `poetry run uvicorn apps.backend.app.api_gateway.main:app --reload`, далее запросы через Postman/HTTPie.

## Админские ручки

### `GET /v1/admin/nodes/{id}/engagement`
Возвращает сводку по карточке ноды. Ответ:
```json
{
  "id": "42",
  "views_count": 120,
  "reactions": {"like": 18},
  "comments": {
    "total": 25,
    "by_status": {"published": 20, "pending": 2, "hidden": 1, "deleted": 2, "blocked": 0},
    "disabled": false,
    "locked": false,
    "locked_by": null,
    "locked_at": null,
    "bans_count": 1
  },
  "links": {
    "moderation": "/v1/admin/nodes/42/moderation",
    "comments": "/v1/admin/nodes/42/comments",
    "analytics": "/v1/admin/nodes/42/analytics",
    "bans": "/v1/admin/nodes/42/comment-bans"
  }
}
```

### `GET /v1/admin/nodes/{id}/comments`
Параметры: `view` (`roots`, `children`, `all`, `thread`), `parentId`, `status`, `authorId`, `createdFrom`, `createdTo`, `search`, `includeDeleted`, `limit`, `offset`, `order` (`desc` по умолчанию). Возвращает список комментариев, сводку по статусам, пагинацию и текущие фильтры.

### `POST /v1/admin/nodes/{id}/comments/lock`
Запрос: `{"locked": true, "reason": "maintenance"}`. Ответ содержит обновлённую сводку и состояние блокировки.

### `POST /v1/admin/nodes/{id}/comments/disable`
Запрос: `{"disabled": true, "reason": "cooldown"}`. Ответ аналогичен ручке блокировки.

### `POST /v1/admin/nodes/comments/{comment_id}/status`
Меняет статус комментария (`published`, `hidden`, `pending`, `blocked`, `deleted`) с опциональной причиной. Возвращает обновлённый комментарий и сводку.

### `DELETE /v1/admin/nodes/comments/{comment_id}`
По умолчанию мягкое удаление, `hard=true` — полное. Опционально принимает `reason`.

### Управление банами
- `GET /v1/admin/nodes/{id}/comment-bans` — активные баны (пользователь, установивший бан, причина, дата).
- `POST /v1/admin/nodes/{id}/comment-bans` — создание/обновление бана: `{ "target_user_id": "uuid", "reason": "spam" }`.
- `DELETE /v1/admin/nodes/{id}/comment-bans/{user_id}` — снятие бана.

Все запросы требуют валидных UUID и заголовка `X-Admin-Key`.

### `GET /v1/admin/nodes/{id}/analytics`
Возвращает агрегированную статистику по просмотрам, лайкам и комментариям.

Параметры:
- `start`, `end` — ISO8601 (UTC);
- `limit` — количество дневных бакетов (по умолчанию 30, максимум 365);
- `format=csv` — получение данных в виде файла (`bucket_date,views,total_likes,total_comments`).

JSON-ответ:
```json
{
  "id": "42",
  "range": {"start": "2025-09-01T00:00:00Z", "end": "2025-09-30T23:59:59Z"},
  "views": {
    "total": 120,
    "buckets": [{"bucket_date": "2025-09-30", "views": 6}],
    "last_updated_at": "2025-09-30T15:05:00Z"
  },
  "reactions": {"totals": {"like": 18}, "last_reaction_at": "2025-09-30T12:00:00Z"},
  "comments": {"total": 25, "by_status": {"published": 20, "pending": 2, "hidden": 1, "deleted": 2, "blocked": 0}},
  "delay": {"seconds": 120, "calculated_at": "2025-09-30T15:05:10Z", "latest_at": "2025-09-30T15:03:10Z"}
}
```

> Совет: передавайте `X-Actor-Id` с UUID администратора, чтобы аудит корректно записывал инициатора. При отсутствии заголовка используется системный актор.
