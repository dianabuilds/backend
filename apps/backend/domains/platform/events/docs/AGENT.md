# Agent Guide — Platform Events

Цель: держать единый интерфейс событий для доменов, а конкретные транспорты (Redis Streams, in‑memory, SQL‑outbox) скрывать за адаптерами платформы.

Куда смотреть
- `ports.py` — протоколы `OutboxPublisher`, `EventBus`, `Handler`.
- `service.py` — фасад `Events` с методами `publish()`, `on()`, `run()`.
- `adapters/` — реализации (Redis EventBus/Outbox, InMemory EventBus).
- `logic/` — политики доставки: идемпотентность, rate‑limit, relay‑цикл.
- `packages/schemas/events/**` — JSON‑схемы событий и версии тем.

Правила
- Доменный код использует только порты из `application/*`. Не импортировать адаптеры платформы напрямую из `domain/*`.
- Новое событие — фиксируйте тему `context.entity.action.vN` и схему в `packages/schemas/events/**`. Валидируйте на паблише и при обработке.
- В проде используем Redis EventBus. In‑memory — только для тестов/локалки.
- Если меняете SQL‑модель и публикуете событие — используйте SQL‑outbox и фоновую выгрузку в Redis.

Настройки (см. `packages/core/config.py`)
- `APP_EVENT_TOPICS` — CSV тем подписки; `APP_EVENT_GROUP` — consumer group.
- `APP_EVENT_RATE_QPS`, `APP_EVENT_IDEMPOTENCY_TTL` — политика доставки.

