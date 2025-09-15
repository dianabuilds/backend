# Platform Search

Внутренний поиск: in‑memory индекс (TF‑IDF), кэш (Redis/in‑memory), snapshot на диск.

- Порты: `ports.py` (`IndexPort`, `QueryPort`, `SearchCache`, `SearchPersistence`)
- Адаптеры: `adapters/memory_index.py`, `adapters/cache_{memory,redis}.py`, `adapters/persist_file.py`
- Сервис: `application/service.py`
- API: `api/http.py` — `GET /v1/search`, `POST /v1/search/index`, `DELETE /v1/search/{id}`, `GET /v1/search/suggest`, `GET /v1/search/stats/top`
- DI: `wires.py` — загрузка snapshot при старте, кэш Redis при наличии `APP_REDIS_URL`

## TODO
- Батч‑сохранение snapshot (дебаунс), бэкап/restore.
- Индексация других доменов по событиям (`nodes.*`, `worlds.*`).
- Синонимы/сте́минг для языков.
- Приватные документы (фильтры по доступу), роли.

