# Platform Quota

Кросс‑доменный лимитер потребления ресурсов.

- Порт DAO: `ports/dao.py`
- Сервис: `application/service.py` (`QuotaService.consume`)
- Адаптер: `adapters/redis_dao.py`
- API: `api/http.py` (`POST /v1/quota/consume`)
- Проводка: `wires.py`

Семантика результата: `allowed`, `remaining`, `limit`, `scope`, `reset_at`, `overage`.

