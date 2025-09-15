# AGENT — Admin Facade

Где править:
- API: `api/http.py` — `/v1/admin/{health,readyz,config}` (guarded by `require_admin`).

Идеи для расширения:
- `/v1/admin/status` — ping Redis/DB, queued events, версии пакетов.
- Операции: инвалидация кэшей, провиженинг (по флагу окружения).

