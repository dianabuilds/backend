# AGENT — Feature Flags

Где править:
- Модель/порт: `domain/models.py`, `ports.py`
- Хранилище: `adapters/store_{memory,redis}.py`
- Сервис: `application/service.py`
- API: `api/http.py`
- DI: `wires.py`

Правила:
- Admin‑guard + CSRF на мутации `/v1/flags`.
- Оценка флага зависит от `enabled`, таргетинга `users/roles` и процентного `rollout`.

