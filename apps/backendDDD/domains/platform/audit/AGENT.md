# AGENT — Audit

Где править:
- Модель: `domain/audit.py`
- Порты/репозитории: `ports/repo.py`, `adapters/repo_{memory,sql}.py`
- Сервис: `application/service.py`
- API: `api/http.py` (`GET/POST /v1/audit`)
- Миграции: `schema/sql/001_create_audit_logs.sql`

Правила:
- Admin‑guard на чтение/запись, CSRF на запись.
- SQL‑репозиторий совместим с легаси моделью `audit_logs`.

