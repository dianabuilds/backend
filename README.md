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
