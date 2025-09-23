# Platform Audit

Сквозной аудит действий пользователей/системы.

- Модель: `domain/audit.py`
- Порт: `ports/repo.py`
- Сервис: `application/service.py`
- Адаптеры:
  - In-memory: `adapters/repo_memory.py`
  - SQL (Postgres): `adapters/repo_sql.py` — использует SQLAlchemy Core (async)
- API: `api/http.py`
  - `GET /v1/audit?limit=100`
  - `POST /v1/audit` (для внутренних вызовов/демо)
- Миграции: `schema/sql/001_create_audit_logs.sql`

## Использование SQL-репозитория

1) Примените миграцию на PostgreSQL:

psql $DATABASE_URL -f apps/backend/domains/platform/audit/schema/sql/001_create_audit_logs.sql

2) Соберите контейнер домена с SQL репозиторием (пример DI):

from sqlalchemy.ext.asyncio import create_async_engine
from apps.backend.domains.platform.audit.adapters.repo_sql import SQLAuditRepo
from apps.backend.domains.platform.audit.application.service import AuditService

engine = create_async_engine(str(settings.database_url))
repo = SQLAuditRepo(engine)
service = AuditService(repo)

3) Подключите в `app/api_gateway/wires.py` вместо in-memory (по желанию).

## TODO
- Фильтры в API (actor/action/resource/period)
- Guard на эндпоинты (только admin/IAM)
- Публикация событий `audit.logged.v1` для downstream
- Хранение workspace_id/override при необходимости

