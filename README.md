# Backend сервис

[![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)

Современный асинхронный бэкенд на FastAPI и SQLAlchemy 2.0 с поддержкой:
- Аутентификации по логину/паролю (JWT) и EVM‑подписей
- Пользовательских профилей, ролей и премиум‑статусов
- Контентных узлов с тегами, переходами, метриками и эмбеддингами
- Модерации, уведомлений, квестов/достижений и платежей

## CI

- PR в ветки `main` и `develop` запускают линтеры (`ruff`), проверку форматирования (`black --check`), типизацию (`mypy`), миграции `alembic upgrade head` и тесты `pytest`.
- Push в `main` дополнительно собирает и публикует Docker‑образ в GHCR.

## Архитектура
Краткое описание основных компонент приведено ниже. Детали см. в [docs/architecture.md](docs/architecture.md).

- FastAPI в качестве веб‑фреймворка
- SQLAlchemy (async) + PostgreSQL/pgvector
- Слои моделей, репозиториев и сервисов
- Движок навигации (compass/echo/random) и кеш Redis
- WebSocket‑уведомления и SMTP‑почта
- Подсистема квестов и достижений
- Платежный модуль для покупки премиума

## Локальная установка
Пошаговая инструкция находится в [docs/local_setup.md](docs/local_setup.md). Кратко:
1. Создайте виртуальное окружение и установите зависимости `pip install -r requirements.txt`.
2. Скопируйте `.env.example` в `.env` и заполните переменные окружения (БД, JWT, SMTP, CORS, Redis, Sentry, Embeddings).
3. Запустите PostgreSQL с расширением pgvector и примените миграции `alembic upgrade head`.
4. Запустите сервер разработки `uvicorn app.main:app --reload` и откройте Swagger на `/docs`.

## Деплой в production
Рекомендации по продакшн‑запуску описаны в [docs/deployment.md](docs/deployment.md). Основной чек‑лист:
1. Сгенерируйте уникальные `JWT__SECRET` и `PAYMENT__JWT_SECRET`.
2. Установите реальные параметры БД и удалите значения `change_me`.
3. Ограничьте `CORS_ALLOWED_ORIGINS` доверенными доменами и настройте защищённые cookie.
4. Выполните Alembic‑миграции и настройте расширение `pgvector`.
5. Укажите `SENTRY_DSN`, уровни логирования и подключите мониторинг.

## Зависимости и запуск
- Python 3.13+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Passlib, PyJWT, Jinja2
- Конфигурационные файлы: `.env`, `.env.example`, `alembic.ini`, `requirements.txt`
- Запуск:
  - Dev: `uvicorn app.main:app --reload`
  - Prod: `gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000`
- Тесты: `pytest`

## Настройка почты
Отправка писем реализована через SMTP. Все параметры настраиваются через переменные окружения с префиксом `SMTP_`.

- `SMTP_MOCK` — если `True`, письма не отправляются, а только логируются (используйте в dev/staging)
- `SMTP_HOST` — адрес SMTP‑сервера
- `SMTP_PORT` — порт сервера
- `SMTP_USERNAME` — логин или имя пользователя
- `SMTP_PASSWORD` — пароль или API‑ключ
- `SMTP_TLS` — включить TLS при подключении
- `SMTP_MAIL_FROM` — адрес отправителя
- `SMTP_MAIL_FROM_NAME` — имя отправителя

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

## Настройка эмбеддингов
Для использования внешних провайдеров эмбеддингов задайте переменные окружения. Пример для AIML API:
```
EMBEDDING_PROVIDER=aimlapi
EMBEDDING_API_BASE=https://api.aimlapi.com/v1/embeddings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=<ваш ключ>
EMBEDDING_DIM=384
```
Реальный ключ храните только в локальном `.env` (файл игнорируется git).

## API документация
Swagger доступен по адресу `http://localhost:8000/docs`, Redoc — `http://localhost:8000/redoc`.
