# Platform Events — Domain Overview

Назначение: кросс‑доменная доставка событий с единой семантикой и интерфейсами. Основной транспорт — Redis Streams, поддержка in‑memory (тесты) и SQL‑outbox для атомарности с БД.

Компоненты
- Порты: `OutboxPublisher`, `EventBus` (см. `ports.py`).
- Фасад: `Events` (`service.py`) — публикация/подписка/запуск доставки.
- Транспорты: `adapters/event_bus_redis.py`, `adapters/event_bus_memory.py`.
- Публикация: `adapters/outbox_redis.py` (низкоуровневый core в `packages/core/redis_outbox.py`).
- Политики: `logic/relay.py`, `logic/idempotency.py`, `logic/policies.py`.

Контракты
- Имя темы: `context.entity.action.vN` (пример: `profile.updated.v1`).
- Схемы: JSON‑Schema в `packages/schemas/events/**`; валидация на паблише и при консьюме.
- Доставка: как минимум один раз. Порядок — per `key` в пределах одной темы.
- Идемпотентность: ключ строится из `(topic, key, payload_hash)`.

Операция
- Прод: Redis Streams с consumer groups, ack, DLQ, rate‑limit.
- Наблюдаемость: метрики xlen/pending, DLQ, логирование ошибок.
- Настройки: `APP_EVENT_TOPICS`, `APP_EVENT_GROUP`, `APP_EVENT_RATE_QPS`, `APP_EVENT_IDEMPOTENCY_TTL`.

