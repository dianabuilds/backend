backend (demo)

Цель: минимальный каркас для старта разработки с ИИ‑агентом.

Слои: api → application → domain → adapters. Публичные контракты в packages/schemas, генерация клиентов в packages/clients. Per‑domain миграции, общий сборщик в infra/ci.

Среда:
- Файл `apps/backend/.env` (пример):
  - `DATABASE_URL=postgresql://app:app@localhost:5432/app`
  - `APP_DATABASE_SSL_CA=apps/backend/infra/certs/rootCA.pem` (при необходимости доверенного сертификата)
  - `REDIS_URL=redis://localhost:6379/0`
  - `NOTIFICATIONS_RETENTION_DAYS=90` (хранение инбокса, по умолчанию 90 дней)
  - `NOTIFICATIONS_MAX_PER_USER=200` (максимум записей на пользователя, по умолчанию 200)

События:
- Публикация в Redis Streams (`events:<topic>`), см. `packages/core/redis_outbox.py`.
- Релей: `make run-relay` (читает `EVENT_TOPICS`, по умолчанию `profile.updated.v1`).

Dev: ручная публикация события
- Через HTTP (нужен `X-Admin-Key` в заголовке, задайте `APP_ADMIN_API_KEY` в `.env`):
  - POST `http://localhost:8000/v1/events/dev/publish`
  - Body:
    { "topic": "node.tags.updated.v1", "payload": { "author_id": "<uuid>", "content_type": "node", "added": ["python"], "removed": [] } }
  - Headers: `X-Admin-Key: <APP_ADMIN_API_KEY>` (Ops контур ожидает `X-Ops-Key: <APP_OPS_API_KEY>``)

- Через CLI-скрипт:
  - Пример:
    python apps/backend/infra/dev/publish_event.py --topic node.tags.updated.v1 --payload '{"author_id":"00000000-0000-0000-0000-000000000001","content_type":"node","added":["python"],"removed":[]}'
  - Использует Redis URL из настроек (переменная `APP_REDIS_URL`).

Проверка счётчиков тегов (SQL)
- После публикации события проверьте таблицу `product_tag_usage_counters`:
  SELECT * FROM product_tag_usage_counters WHERE author_id = '<uuid>' ORDER BY slug;

## Установка пакета

```bash
cd apps/backend
python -m pip install -e .
```

Команда устанавливает backend как локальный пакет и упрощает запуск mypy/pytest из любой директории.

