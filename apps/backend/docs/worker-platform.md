# Worker Platform

## Что уже готово

- инфраструктура пакета `packages.worker`: базовый класс, periodic-воркер, регистрация и CLI (`python -m packages.worker.runner`).
- Control-plane для задач: REST API `/v1/worker/jobs*`, Postgres-репозиторий c lease и optional Redis-очередью.
- Готовый доменный пример `notifications.broadcast`, оркестратор рассылок и воркер, который сканирует due-брасдкасты.
- Метрики воркеров доступны через `/v1/admin/telemetry/summary` и `/v1/admin/telemetry/prometheus`.

## Быстрый сценарий: рассылки уведомлений

1. **Окружение**
   - примените миграции `alembic upgrade head`;
   - запустите Redis, если хотите использовать очередь push/pop для других воркеров;
   - выставьте `PYTHONPATH=apps/backend` (или запускайте из Makefile).
2. **Создайте рассылку** (пример запроса, требуется админская авторизация и CSRF токен):
   ```bash
   curl -X POST http://localhost:8000/v1/admin/notifications/broadcasts \
     -H 'Content-Type: application/json' \
     -H 'X-CSRF-Token: <token>' \
     -d '{
       "title": "Feature launch",
       "body": "We are live!",
       "created_by": "ops",
       "audience": { "type": "all_users" },
       "scheduled_at": "2025-09-26T12:00:00Z"
     }'
   ```
   Ответ вернёт `id`. Для немедленного запуска вызовите:
   ```bash
   curl -X POST http://localhost:8000/v1/admin/notifications/broadcasts/<id>/actions/send-now \
     -H 'X-CSRF-Token: <token>'
   ```
3. **Запустите воркер**
   ```bash
   PYTHONPATH=apps/backend \
   NOTIFICATIONS_BROADCAST_INTERVAL=15 \
   python -m packages.worker.runner --name notifications.broadcast --log-level=INFO
   ```
   Переменные окружения:
   - `NOTIFICATIONS_BROADCAST_INTERVAL` (секунды между тиками);
   - `NOTIFICATIONS_BROADCAST_JITTER` (±секунды шума);
   - `NOTIFICATIONS_BROADCAST_BATCH_LIMIT` (макс. рассылок за тик);
   - `NOTIFICATIONS_BROADCAST_IMMEDIATE=0/1` (делать ли первый тик сразу при старте).

Воркер берёт due-рассылки, помечает их `sending`, доставляет события в inbox и логирует результат. После выполнения статусы таблицы `notification_broadcasts` обновляются (total/sent/failed), а асинхронные подключения к БД закрываются при остановке.

## Наблюдаемость и здоровье

- `/v1/admin/telemetry/summary` (SPA использует на странице Observability) — поле `workers.jobs` показывает счётчики `started/completed/failed`.
- `/v1/admin/telemetry/prometheus` — текстовые метрики `ai_worker_jobs_total{status=...}` и `ai_worker_stage_avg_ms{stage="notifications.broadcast"}` (название совпадает с worker name).
- Логи воркера: `broadcast <id> completed status=sent ...` или `failed`, чтобы быстро увидеть объём рассылки.
- Для диагностики очереди используйте REST API worker control-plane (`POST /v1/worker/jobs`, `.../lease`, `.../complete`, `.../fail`). Уведомления пока работают как периодический воркер, но инфраструктура очереди готова для фичевых воркеров.

## Что дальше

- Подключить дополнительные воркеры по фичам: реализуйте доменную логику, зарегистрируйте builder через `@register_worker`, при необходимости используйте `WorkerQueueService` для джобов.
- Добавить более подробные метрики (время стадий, объём обработанных пользователей) через `worker_metrics.observe_stage`/`observe_job`.
- Настроить алерты на превышение `failed` и длительных тиков, а также визуализацию очередей в Observability.
