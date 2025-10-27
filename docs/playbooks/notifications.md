# Notifications Monitoring & Runbook

## Ключевые метрики

| Метрика | Описание | Источник/пример |
| --- | --- | --- |
| `pg_class_relation_size_bytes{relname="notification_receipts"}` | Размер таблицы `notification_receipts` | PostgreSQL exporter |
| `pg_class_relation_size_bytes{relname="notification_messages"}` | Размер таблицы `notification_messages` | PostgreSQL exporter |
| `ai_worker_jobs_total{status="retention_runs"}` | Количество прогонов очистки | Cron/worker metrics |
| `ai_worker_jobs_total{status="retention_removed_age"}` | Удалено по лимиту возраста | Cron/worker metrics |
| `ai_worker_jobs_total{status="retention_removed_limit"}` | Удалено по лимиту (per-user) | Cron/worker metrics |
| `ai_worker_jobs_total{status="retention_removed_messages"}` | Очищено осиротевших сообщений | Cron/worker metrics |
| `ai_worker_jobs_total{status="failed"}` | Ошибки воркера (доставка/очистка) | Cron/worker metrics |
| `ai_worker_stage_avg_ms{stage="notifications.broadcast"}` | Средняя длительность этапов рассылки | Cron/worker metrics |

> Метрики `worker_counter_total` и `worker_stage_avg_ms` публикуются через существующий endpoint `worker_metrics.prometheus()`.

## Рекомендованные панели Grafana

1. **Storage** — размер таблиц (`notification_receipts`, `notification_messages`), их суточный derivative.
2. **Retention** — stat panels по последним значениям `ai_worker_jobs_total{status="retention_runs"}`, `..._removed_*`, график удалений в сутки.
3. **Delivery Worker** — gauge/graph по `ai_worker_jobs_total` (started/completed/failed), latency `ai_worker_stage_avg_ms`.
4. **Inbox Activity** — количество созданных уведомлений (`increase(worker_counter_total{status="started"}[1d])`), рассылка по приоритетам (при появлении отдельных метрик).

## Алерты

| Алерт | Условие | Реакция |
| --- | --- | --- |
| `NotificationsRetentionStuck` | `increase(ai_worker_jobs_total{status="retention_runs"}[6h]) == 0` и рост размера `notification_receipts` > 10% | Проверить воркер, запустить ручной prune |
| `NotificationsWorkerDown` | `increase(ai_worker_jobs_total{status="started"}[15m]) == 0` | Перезапустить воркер, изучить логи |
| `NotificationStorageHigh` | `pg_class_relation_size_bytes{relname="notification_receipts"}` > 80% от лимита или derivative > 500 МБ/сутки | Скорректировать retention / расширить диск |
| `NotificationDeliveryFailures` | `increase(ai_worker_jobs_total{status="failed"}[1h]) > 0` | Проверить логи, временно отключить канал |

## Playbook

### Обновить конфигурацию retention через API
1. Запросить текущие значения: `GET /v1/settings/notifications/retention` (доступ только для `require_admin`). Ответ содержит JSON со структурой:
   ```json
   {
     "retention_days": 90,
     "max_per_user": 200,
     "updated_at": "2025-10-27T12:40:11Z",
     "updated_by": "1575f1f4-b5a5-4d6c-9c3e-1b19d53a642a",
     "source": "database"
   }
   ```
   Если `source = "settings"`, используется fallback из `notifications.retention_days|max_per_user` в конфиге.
2. Сохранить заголовок `ETag` и отправить PUT:
   ```bash
   curl -X PUT https://admin.caves.local/v1/settings/notifications/retention \
     -H "Authorization: Bearer <admin token>" \
     -H "Idempotency-Key: <uuid>" \
     -H "If-Match: <etag из шага 1>" \
     -H "Content-Type: application/json" \
     --data '{"retention_days":120,"max_per_user":300}'
   ```
   Поля `retention_days` и `max_per_user` принимают значения `1..365` и `1..1000`. `null` или `0` отключают параметр и возвращают fallback.
3. Убедиться, что ответ вернул новый `ETag` и актуальный JSON. Сервис сам обновит DeliveryService (`update_retention`), перезапуск воркера не нужен.
4. Проверить аудит: событие `notifications.retention.updated` (resource `notifications`, before/after с конфигурацией). Если аудит временно недоступен, зафиксировать изменение вручную в `reports/<дата>/`.

### Ручная очистка
```python
from apps.backend.domains.platform.notifications.adapters.sql.notifications import NotificationRepository
repo = NotificationRepository("postgresql+asyncpg://app:app@localhost:5432/app")
await repo.prune(retention_days=90, max_per_user=200)
```
После выполнения проверить размеры таблиц и метрики. При необходимости выполнить `VACUUM (ANALYZE)`/`REINDEX` (через DBA).

### Откатить изменения retention
1. Найти прежние значения в аудит-логе (`notifications.retention.updated`) или напрямую: `SELECT value FROM notification_config WHERE key = 'retention'`.
2. Повторить PUT с `Idempotency-Key` и `If-Match`, передав сохранённый JSON.
3. Чтобы вернуться к конфигурации из настроек, отправить `{"retention_days": null, "max_per_user": null}` — в ответе `source` снова станет `"settings"`.
4. Проверить `ai_worker_jobs_total{status="retention_runs"}` и лог `notifications retention cleaned`, убедиться, что лимиты применились.

### Диагностика роста
1. Проверить dashboard Storage/Retention.
2. Если `retention_runs` = 0 → воркер не запускает prune (перезапустить, изучить логи).
3. Если prune идёт, а размер не уменьшается → увеличить `NOTIFICATIONS_BROADCAST_BATCH_LIMIT` или провести ручную очистку в несколько проходов.
4. При продолжении роста — проверить, не отключены ли индексы, нет ли постоянных ошибок в логах.

### Проблемы доставки
1. Проверить `worker_counter_total{status="failed"}` и логи (`notification_push_failed`, `notifications retention failed`).
2. Убедиться, что WebSocket клиенты подключаются (Topbar, `/v1/notifications/ws`).
3. При необходимости временно отключить конкретный канал через настройки.

## Ссылки
- `apps/backend/README.md` — fallback-параметры `notifications.retention_days`, `notifications.max_per_user`.
- `apps/backend/domains/platform/notifications/application/retention_service.py` — нормализация значений и ограничения.
- `apps/backend/domains/platform/notifications/adapters/sql/config.py` — работа с таблицей `notification_config`.
- `apps/backend/migrations/versions/0115_notifications_retention_config.py` — схема `notification_config`.
- `apps/backend/domains/platform/notifications/workers/broadcast.py` — логика воркера и очистки.
- `apps/backend/app/api_gateway/settings/notifications.py` — эндпоинты `/v1/settings/notifications/retention` и аудит `notifications.retention.updated`.
- `apps/web/src/features/notifications/inbox` — клиентский UI для проверки realtime-доставки.
