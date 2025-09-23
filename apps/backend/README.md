backend (demo)

Цель: минимальный каркас для старта разработки с ИИ‑агентом.

Слои: api → application → domain → adapters. Публичные контракты в packages/schemas, генерация клиентов в packages/clients. Per‑domain миграции, общий сборщик в infra/ci.

Среда:
- Файл `apps/backend/.env` (пример):
  - `DATABASE_URL=postgresql://app:app@localhost:5432/app`
  - `REDIS_URL=redis://localhost:6379/0`

События:
- Публикация в Redis Streams (`events:<topic>`), см. `packages/core/redis_outbox.py`.
- Релей: `make run-relay` (читает `EVENT_TOPICS`, по умолчанию `profile.updated.v1`).

Dev: ручная публикация события
- Через HTTP (нужен `X-Admin-Key` в заголовке, задайте `APP_ADMIN_API_KEY` в `.env`):
  - POST `http://localhost:8000/v1/events/dev/publish`
  - Body:
    { "topic": "node.tags.updated.v1", "payload": { "author_id": "<uuid>", "content_type": "node", "added": ["python"], "removed": [] } }
  - Headers: `X-Admin-Key: <APP_ADMIN_API_KEY>`

- Через CLI-скрипт:
  - Пример:
    python apps/backend/infra/dev/publish_event.py --topic node.tags.updated.v1 --payload '{"author_id":"00000000-0000-0000-0000-000000000001","content_type":"node","added":["python"],"removed":[]}'
  - Использует Redis URL из настроек (переменная `APP_REDIS_URL`).

Проверка счётчиков тегов (SQL)
- После публикации события проверьте таблицу `product_tag_usage_counters`:
  SELECT * FROM product_tag_usage_counters WHERE author_id = '<uuid>' ORDER BY slug;
