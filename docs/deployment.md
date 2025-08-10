# Деплой в production

1. **PostgreSQL + pgvector**
   - Установите PostgreSQL и расширение `pgvector`:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     ```
   - Настройте параметры подключения через переменные `DB_*`.
2. **Миграции**
   ```bash
   alembic upgrade head
   ```
3. **Эмбеддинги**
   - Укажите провайдера и ключи (`EMBEDDING_PROVIDER`, `EMBEDDING_API_KEY`).
   - Убедитесь, что размерность `EMBEDDING_DIM` соответствует колонке в БД.
4. **Платежный провайдер**
   - Настройте секреты `PAYMENT_JWT_SECRET` или `PAYMENT_WEBHOOK_SECRET`.
   - Реализуйте проверку webhook'ов в `app/services/payments.py`.
5. **Безопасность CORS и cookies**
   - Ограничьте `CORS_ALLOWED_ORIGINS` доверенными доменами.
   - Установите `COOKIE_SECURE=True` и задайте `COOKIE_DOMAIN`.
6. **Sentry, логирование и мониторинг**
   - Задайте `SENTRY_DSN` и `SENTRY_ENV`.
   - Настройте уровни `LOG_LEVEL` и `REQUEST_LOG_LEVEL`.
   - Интегрируйте внешний мониторинг (Prometheus, Grafana, APM) при необходимости.
7. **Запуск приложения**
   ```bash
   gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```
8. **Проверка**
   - Убедитесь, что `/health` возвращает `200` и что метрики/логи собираются корректно.
