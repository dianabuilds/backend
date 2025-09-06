# Backend сервис

Асинхронный backend на FastAPI и SQLAlchemy 2.0. Сервис предоставляет REST и WebSocket API для работы с пользователями, контентными узлами и AI‑подсистемой.

## Возможности
- Аутентификация по паролю и EVM‑подписей
- Профили пользователей, роли и премиум‑статусы
- Узлы контента с тегами, переходами и эмбеддингами
- Модерация, уведомления и платёжный модуль

## Быстрый старт
1. Создать виртуальное окружение и установить зависимости:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt -c constraints/py311-max.txt
   ```
2. Создать файл `.env` на основе `.env.example` и заполнить переменные окружения.
   Примеры конфигураций для разных сред и правила cookies описаны в `docs/environment.md`.
3. Инициализировать базу данных:
   ```bash
   python scripts/init_db.py
   ```
4. Запустить сервер разработки:
   ```bash
   python scripts/run.py
   ```
5. Фоновый AI‑воркер:
   ```bash
   python scripts/run_ai_worker.py
   ```
6. Заполнить базу тестовыми данными:
   ```bash
   python scripts/seed_db.py --users 5 --nodes 30
   ```
7. Проверить запуск сервисов:
   ```bash
   python scripts/smoke_check.py
   ```

## Windows Quickstart

1. Создать виртуальное окружение и установить зависимости:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt -c constraints\py311-max.txt
   ```
2. Создать `.env` на основе `.env.example` и инициализировать базу данных:
   ```powershell
   python scripts\init_db.py
   ```
3. Запустить сервер разработки:
   ```powershell
   python scripts\run.py
   ```
4. (Опционально) запустить AI‑воркер:
   ```powershell
   python scripts\run_ai_worker.py
   ```

## Environment modes

Поддерживаются несколько режимов окружения, влияющих на политику безопасности,
провайдеров и уровень строгих проверок. Режим задаётся переменной
`ENVIRONMENT` (`development`, `staging`, `production`). Некоторые ключевые
переменные:

| Переменная             | Значение по умолчанию                         | Описание                                         |
|------------------------|-----------------------------------------------|--------------------------------------------------|
| `ENVIRONMENT`          | `development`                                 | текущий режим работы приложения                  |
| `ALLOW_EXTERNAL_CALLS` | `true` в dev/staging, `false` в prod          | разрешены ли исходящие HTTP/SMTP вызовы          |
| `RNG_SEED_STRATEGY`    | `fixed` в dev/test, `random` в prod           | стратегия генерации случайных чисел              |
| `RNG_SEED`             | –                                             | фиксированное значение для детерминизма          |

Команды запуска:

```bash
python scripts/run.py                 # development mode
```

## Checklists

### Переключение режимов
- [ ] Установить `ENVIRONMENT=development|staging|production`.
- [ ] Запустить сервер (`python scripts/run.py` в разработке).
- [ ] Убедиться по логам, что выбран нужный режим.

### Сидирование данных
- [ ] Настроить `.env` и выполнить миграции (`python scripts/init_db.py`).
- [ ] Запустить `python scripts/seed_db.py --users 5 --nodes 30`.
- [ ] При необходимости очистить базу флагом `--wipe`.

### Политика внешних вызовов
- [ ] Контролировать исходящие запросы переменной `ALLOW_EXTERNAL_CALLS`.
- [ ] В продакшене по умолчанию отключать внешние вызовы.
- [ ] Включать их только для доверенных интеграций.

### Determinism
- [ ] Для воспроизводимых результатов задавать `RNG_SEED` или `--seed`.
- [ ] Использовать стратегию `RNG_SEED_STRATEGY=fixed` при тестировании.
- [ ] Избегать сторонних сервисов, влияющих на результат.

## accounts и лимиты

- Создайте рабочее пространство:
  ```bash
  http POST :8000/admin/accounts/123e4567-e89b-12d3-a456-426614174000 name=Demo slug=demo
  ```
- Все запросы к контенту выполняются через префикс рабочего пространства:
  ```bash
  http GET :8000/admin/accounts/123e4567-e89b-12d3-a456-426614174000/nodes/all
  ```
- Лимиты запросов настраиваются переменными `RATE_LIMIT_*` в `.env`.
- Импортируйте коллекцию `docs/postman_collection.json` или используйте `docs/httpie_examples.sh` для быстрого теста API.

## Форматирование и тестирование

- `pre-commit install`
- `pre-commit run --all-files`
- `pytest` для бэкенда; `pnpm test` для фронтенда

Пример рабочего цикла: изменить файл → `pre-commit run --files <file>` → `pytest -k <module>` или `pnpm test <path>` → `git commit`.

CI повторно запускает те же проверки, поэтому локальный прогон экономит время.

## Сканирование зависимостей
CI запускает проверки уязвимостей через `pip-audit` для Python и `npm audit` для Node. Локально запустить их можно так:

```bash
pip install pip-audit && pip-audit -r requirements.txt -c constraints/py311-max.txt
cd apps/admin && npm audit
```

Пайплайн падает при критических уязвимостях, а отчёты сохраняются как артефакты CI для отслеживания ремедиации.

Дополнительно в GitHub Actions публикуются артефакты:

- `reports/validate_repo.md` — сводка линтеров, типизации и базового бенчмарка (`scripts/validate_repo.py`).
- `sbom.json` — программная ведомость (SBOM) в формате CycloneDX.

Оба файла доступны в разделе Artifacts каждого прогона `ci.yml`.

## Troubleshooting

- `ModuleNotFoundError`: убедитесь, что виртуальное окружение активировано и зависимости установлены.
- Ошибки при сборке `psycopg`: установите инструменты компиляции или используйте `pip install psycopg[binary]`.
- Нет подключения к базе: проверьте, что PostgreSQL запущен и переменные в `.env` корректны.

## Миграции

Подробное руководство по созданию и проверке миграций находится в [docs/migrations.md](docs/migrations.md).
После обновления репозитория выполните последнюю миграцию для
добавления отсутствующих записей `content_items`:

```bash
alembic upgrade head
```

## Структура проекта
- `apps/backend/app` – код приложения и доменные модули
- `apps/backend/alembic` – миграции базы данных
- `apps/admin` – исходники SPA админской панели
- `scripts` – вспомогательные скрипты
- `docs` – документация и руководства

## Лицензия
Проект распространяется под лицензией MIT.
