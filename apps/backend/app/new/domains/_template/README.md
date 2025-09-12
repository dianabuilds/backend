
# PRODUCT DOMAIN TEMPLATE

Миссия: описать продуктовый домен с чёткими границами, внутренними моделями и публичными контрактами,
которые **хранятся за пределами домена** в `/packages/schemas`.

## Границы
- Владеет: агрегатами, политиками, внутренними DTO, сервисами, репозиториями.
- Не владеет: публичными схемами API/событий (они в `/packages/schemas`), IAM-правилами, платёжной логикой и т.п.

## Где лежат контракты
- OpenAPI домена: `/packages/schemas/api/<domain>.v1.yaml`
- События домена: `/packages/schemas/events/<domain>.*.v1.json`

## Быстрый старт
- API-роутер: `api/http.py` (FastAPI Router)
- Сервисы: `application/services/*`
- Политики: `application/policies.py`
- Outbox: `infrastructure/outbox.py`
- Репозитории: `infrastructure/repositories/*`
- Evals/агент: `agent/*`
- Тесты: `tests/*`

Создан: 2025-09-12T17:23:34.526772Z
