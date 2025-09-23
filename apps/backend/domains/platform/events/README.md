# Platform Events

Единый интерфейс событий для доменов с адаптерами под разные транспорты.

- Порты: `ports.py`
- Фасад: `service.py`
- Транспорты: `adapters/event_bus_redis.py`
- Публикация: `adapters/outbox_redis.py`
- Политики: `logic/*`
- Документация: `docs/`

См. `packages/core/config.py` для конфигурации шины и топиков.

