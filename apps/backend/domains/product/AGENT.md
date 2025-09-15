# AGENT — Product Domains

Скелет продуктового домена следует слоям: `api/`, `application/`, `domain/`, `adapters/`.

- Domain: чистые модели/политики, без I/O и FastAPI.
- Application: use‑cases, порты для внешних зависимостей (репозитории, клиенты, outbox).
- Adapters: реализация портов (SQL/HTTP/Redis и т.п.).
- API: FastAPI‑роуты и схемы; зависимости `get_container(req)`.

Интеграции платформы:
- События: публикуйте в `Events` через порт Outbox из слоя application.
- Уведомления/телеметрия/квоты: используйте соответствующие сервисы из контейнера в API/Adapters (не в `domain/`).
- IAM/Безопасность: `get_current_user`, `csrf_protect`, `require_role_db` из `platform/iam/security.py`.
- Rate‑limit: добавляйте `Depends(RateLimiter(...))` при наличии Redis.

Запреты:
- Не импортировать платформенные адаптеры в `domain/`.
- Не ходить напрямую в БД из `api/` (только через application/adapters).

Как добавить домен:
1) Создайте `domains/product/<name>/{api,application,domain,adapters}`.
2) Опишите порты в `application/ports.py` и модели в `domain/*`.
3) Реализуйте адаптеры и `wires.py` под DI контейнер (если нужен).
4) Подключите роутер в `app/api_gateway/main.py` и зависимости в `wires.py`.
5) При необходимости добавьте схемы в `packages/schemas/**` и DDL в `schema/sql/*`.

Links
- Tags: `domains/product/tags/AGENT.md`, `domains/product/tags/docs/DOMAIN.md`
- Quests: `domains/product/quests/AGENT.md`
- Navigation: `domains/product/navigation/AGENT.md`
- AI: `domains/product/ai/AGENT.md`, `domains/product/ai/docs/DOMAIN.md`
