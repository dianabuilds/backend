# Backend сервис

Асинхронный backend на FastAPI и SQLAlchemy 2.0. Сервис предоставляет REST и WebSocket API для работы с пользователями, контентными узлами и AI‑подсистемой.

## Возможности
- Аутентификация по паролю и EVM‑подписей
- Профили пользователей, роли и премиум‑статусы
- Узлы контента с тегами, переходами и эмбеддингами
- Модерация, уведомления и платёжный модуль

## Быстрый старт
1. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Создать файл `.env` на основе `.env.example` и заполнить переменные окружения.
3. Инициализировать базу данных:
   ```bash
   python scripts/init_db.py
   ```
4. Запустить сервер разработки:
   ```bash
   ./scripts/run.sh --dev
   ```
5. Для запуска в продакшене используйте:
   ```bash
   ./scripts/run.sh --prod --workers 4
   ```
6. Фоновый AI‑воркер:
   ```bash
   python scripts/run_ai_worker.py
   ```
7. Заполнить базу тестовыми данными:
   ```bash
   python scripts/seed_db.py --users 5 --nodes 30
   ```
8. Проверить запуск сервисов:
   ```bash
   python scripts/smoke_check.py
   ```

## Workspaces и лимиты

- Создайте рабочее пространство:
  ```bash
  http POST :8000/admin/workspaces/123e4567-e89b-12d3-a456-426614174000 name=Demo slug=demo
  ```
- Все запросы к контенту требуют `workspace_id`:
  ```bash
  http GET :8000/admin/nodes/all workspace_id==123e4567-e89b-12d3-a456-426614174000
  ```
- Лимиты запросов настраиваются переменными `RATE_LIMIT_*` в `.env`.
- Импортируйте коллекцию `docs/postman_collection.json` или используйте `docs/httpie_examples.sh` для быстрого теста API.

## Тесты
```bash
pytest
```

## Структура проекта
- `apps/backend/app` – код приложения и доменные модули
- `apps/backend/alembic` – миграции базы данных
- `apps/admin` – исходники SPA админской панели
- `scripts` – вспомогательные скрипты
- `docs` – документация и руководства

## Лицензия
Проект распространяется под лицензией MIT.
