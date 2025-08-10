# Backend сервис

Современный асинхронный бэкенд на FastAPI и SQLAlchemy 2.0 с поддержкой:
- Аутентификации по логину/паролю (JWT) и EVM-подписей
- Пользовательских профилей, ролей (user/moderator/admin) и премиум-статусов
- Контентных узлов (nodes) с тегами, переходами, метриками и эмбеддингами
- Модерации контента и ограничений для пользователей
- Гибкой подсказки переходов (echo/compass/random) поверх встроенного движка

Проект готов для локальной разработки, тестирования и деплоя.

## Технологический стек

- Python 3.13+
- FastAPI
- SQLAlchemy 2.0 (async) + asyncpg
- Alembic (миграции)
- Pydantic v2 / pydantic-settings
- Passlib (bcrypt) и PyJWT
- Jinja2
- Uvicorn / Gunicorn (ASGI)

## Структура проекта

## Production config

Для запуска в продакшене заполните переменные окружения из `.env.example`.

Ключевые секции:

- **База данных**: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`.
- **JWT и сессии**: `JWT_SECRET`, `JWT_ALG`, `JWT_EXPIRES_MIN`, `COOKIE_DOMAIN`, `COOKIE_SECURE`, `COOKIE_SAMESITE`.
- **Оплаты**: `PAYMENT_JWT_SECRET` или `PAYMENT_WEBHOOK_SECRET` (секреты должны отличаться от `JWT_SECRET`).
- **CORS**: `CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_CREDENTIALS`, `CORS_ALLOWED_METHODS`, `CORS_ALLOWED_HEADERS`.
- **Sentry и логи**: `SENTRY_DSN`, `SENTRY_ENV`, `LOG_LEVEL`, `REQUEST_LOG_LEVEL`, `SLOW_QUERY_MS`.
- **Redis**: `REDIS_URL`, если используете кеш или очереди.

Чек‑лист продакшна:

1. Сгенерируйте случайные значения для `JWT_SECRET` и `PAYMENT_JWT_SECRET`; они **обязаны отличаться**.
2. Задайте реальные параметры базы данных и уберите значения `change_me`.
3. Ограничьте `CORS_ALLOWED_ORIGINS` только доверенными доменами.
4. Включите защищённые cookie (`COOKIE_SECURE=True`, `COOKIE_SAMESITE=Strict` или `Lax`) и задайте `COOKIE_DOMAIN`.
5. Укажите `SENTRY_DSN` и проверьте отправку ошибок.
6. Настройте уровни логирования и порог `SLOW_QUERY_MS`.
7. Выполните миграции и убедитесь, что `/health` возвращает `200`.

## Настройка почты

Отправка писем реализована через SMTP. Все параметры настраиваются через переменные окружения с префиксом `SMTP_`.

- `SMTP_MOCK` — если `True`, письма не отправляются, а только логируются (используйте в dev/staging);
- `SMTP_HOST` — адрес SMTP‑сервера;
- `SMTP_PORT` — порт сервера;
- `SMTP_USERNAME` — логин или имя пользователя;
- `SMTP_PASSWORD` — пароль или API‑ключ;
- `SMTP_TLS` — включить TLS при подключении;
- `SMTP_MAIL_FROM` — адрес отправителя;
- `SMTP_MAIL_FROM_NAME` — имя отправителя.

В разработке оставляйте `SMTP_MOCK=True`. Для боевого окружения установите `SMTP_MOCK=False` и заполните остальные поля.

Пример конфигурации для SendGrid:

```
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=<SG_API_KEY>
SMTP_TLS=True
SMTP_MAIL_FROM=noreply@example.com
SMTP_MAIL_FROM_NAME=Наш новый сайт
```

## Email templates

* Шаблоны лежат в `app/templates`.
* Для каждого письма должна существовать пара файлов `*.html` и `*.txt`.
* Пример вызова:

```python
await mail_service.send_email(
    to=user.email,
    subject="Подтверждение email",
    template="auth/verify_email",  # имя без расширения
    context={"username": user.username, "verify_url": url},
)
```

* Локализация: передайте префикс локали в имени шаблона, например `ru/auth/verify_email`.
* Общие элементы (хедер, футер, кнопки) находятся в `app/templates/_partials` и подключаются через `{% include %}`.
* **Контент:** HTML‑версии со встроенными стилями, текстовые — лаконичные и чистые.

## Настройка эмбеддингов

Для использования внешних провайдеров эмбеддингов задайте переменные окружения.
Пример для AIML API приведён в `.env.example`:

```
EMBEDDING_PROVIDER=aimlapi
EMBEDDING_API_BASE=https://api.aimlapi.com/v1/embeddings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=<ваш ключ>
EMBEDDING_DIM=384
```

Реальный ключ храните только в локальном `.env`, который уже добавлен в `.gitignore`.

