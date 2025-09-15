# Platform Admin Facade

Минимальный фасад для административных эндпоинтов платформы.

- API: `api/http.py`
  - `GET /v1/admin/health` — liveness
  - `GET /v1/admin/readyz` — readiness
  - `GET /v1/admin/config` — основные параметры (без секретов)
  - Все ручки — `require_admin`

## TODO
- `GET /v1/admin/status` — ping Redis/DB, очереди, версии.
- Операции: инвалидация кэшей (опционально, за фичефлагом).

