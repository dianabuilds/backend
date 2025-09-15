# AGENT — Quota

Где править:
- Порт DAO: `ports/dao.py`
- Redis DAO: `adapters/redis_dao.py`
- Сервис: `application/service.py`
- API: `api/http.py` (`POST /v1/quota/consume`)

Правила:
- Расчёт периода day|month, TTL по `reset_at`.
- Возвращает `QuotaResult` и 429 при превышении.

