# Platform Feature Flags

Простые фиче‑флаги с таргетингом по пользователю/роли и процентным rollout.

- Модель: `domain/models.py` (`Flag`)
- Порт: `ports.py` (`FlagStore`)
- Адаптеры: `adapters/store_{memory,redis}.py`
- Сервис: `application/service.py` (оценка и CRUD)
- API: `api/http.py`
  - Admin: `GET/POST/DELETE /v1/flags*` (guard + CSRF)
  - Пользователь: `GET /v1/flags/check/{slug}` — возвращает `{slug,on}`
- DI: `wires.py` — Redis при наличии, иначе in‑memory

## Оценка
1) `enabled == False` → off
2) если `user_id ∈ users` → on
3) если `role ∈ roles` → on
4) процентный rollout по стабильному хешу user_id → on/off

## TODO
- Валидация схем и типизации полей в API
- Экспорт/импорт набора флагов (JSON)
- Admin‑аудит изменений (интеграция с `platform/audit`)
- Метрики по попаданиям/оценкам

