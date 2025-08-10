# Локальная установка и запуск

1. Установите Python 3.13+ и создайте виртуальное окружение:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Скопируйте файл `.env.example` в `.env` и заполните переменные окружения:
   - **База данных**: `DATABASE__HOST`, `DATABASE__PORT`, `DATABASE__NAME`, `DATABASE__USERNAME`, `DATABASE__PASSWORD`.
   - **JWT**: `JWT__SECRET`, `JWT__ALGORITHM`, `JWT__EXPIRES_MIN`.
   - **Cookies**: `COOKIE_DOMAIN`, `COOKIE_SECURE`, `COOKIE_SAMESITE`.
   - **SMTP**: параметры `SMTP_*` для отправки почты или `SMTP_MOCK=True`.
   - **CORS**: `CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_CREDENTIALS`, `CORS_ALLOWED_METHODS`, `CORS_ALLOWED_HEADERS`.
   - **Redis**: `REDIS_URL` при использовании кеша или очередей.
   - **Sentry и логирование**: `SENTRY_DSN`, `SENTRY_ENV`, `LOG_LEVEL`.
   - **Embeddings**: `EMBEDDING_PROVIDER`, `EMBEDDING_API_BASE`, `EMBEDDING_MODEL`, `EMBEDDING_API_KEY`.
3. Запустите PostgreSQL с расширением `pgvector` и создайте базу данных.
4. Примените миграции:
   ```bash
   alembic upgrade head
   ```
5. Запустите приложение в режиме разработки:
   ```bash
   uvicorn app.main:app --reload
   ```
6. Откройте Swagger по адресу `http://127.0.0.1:8000/docs`.
7. Для запуска тестов используйте:
   ```bash
   pytest
   ```
