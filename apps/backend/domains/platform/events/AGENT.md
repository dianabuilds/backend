# AGENT.md — Platform Events

Куда вносить правки:
- Порты (`ports.py`), фасад (`service.py`), адаптеры (`adapters/*`), политики (`logic/*`).
- Не переносить бизнес‑логику продуктовых доменов сюда.

Типичные задачи и куда идти:
- Добавить новый транспорт доставки → `adapters/event_bus_*` + проводка в `wires` приложения.
- Включить/изменить публикацию событий → используйте порт `OutboxPublisher`; для Redis берите `adapters/outbox_redis.RedisOutbox`.
- Подписать обработчик → регистрируйте через `Events.on(topic, handler)`.
- Запустить доставку → `Events.run()` (в воркере/фоновой задаче).

Контракты и схемы:
- Имена тем: `context.entity.action.vN`.
- Схемы событий: `apps/backendDDD/packages/schemas/events/**`.

Конфигурация: см. `apps/backendDDD/packages/core/config.py`.

