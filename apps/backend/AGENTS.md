# Гид для агентов (backend)

Основной ритм: PLAN → TESTS → CODE → SELF-REVIEW. Важно поддерживать схемы и миграции актуальными.

Слои: api → application → domain → adapters. Domain не содержит I/O и FastAPI.

Контракты: храните схемы в pps/backend/packages/schemas/** (OpenAPI/Events). При изменениях — фиксируйте CHANGELOG/MIGRATION.

Полезные команды:
- make schemas-validate / make schemas-compat — валидация схем.
- make test — тесты (если есть).
- make run / make run-events — запуск API / воркера событий.

Минимум документации в домене: AGENT.md, README.md, при необходимости docs/DOMAIN.md.

Правила:
- Архитектура: не импортировать платформенные адаптеры в domain/. В pi/ не ходить напрямую в БД.
- Безопасность: используйте get_current_user, csrf_protect, 
equire_admin/
equire_role_db из platform/iam/security.py.
- События: публикуйте через порт Outbox; добавляйте JSON‑схему в packages/schemas/events/**.
- Rate‑limit: добавляйте Depends(RateLimiter(...)) на write‑ручки (если есть Redis).
- Миграции: добавляйте DDL в domains/<ctx>/schema/sql/*.sql; не ломайте обратную совместимость без нужды.

Для продуктовых доменов: см. domains/product/AGENT.md (интеграция с платформой, порты, wires и валидация контрактов).
