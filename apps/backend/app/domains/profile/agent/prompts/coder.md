# Coder Prompt — Profile

Следуй этому чек‑листу при любых изменениях в домене Profile.

1) Scope
- Меняешь только код в `app/domains/profile/**` и `app/schemas/profile.py`.
- Роутер уже подключён в `app/domains/registry.py` — не дублировать.

2) Контракты и схемы
- Первым делом обнови `schema/openapi.yaml` при изменении API.
- Синхронизируй модели `ProfileOut`/`ProfileUpdate` и ручки.
- API изменения — только ап‑совместимые.

3) События
- При PATCH профиля публикуем `event.profile.updated.v1` через outbox.
- Добавление полей в событие допустимо; breaking → новая версия `.vN+1` и новый паблишер.

4) Политики/инварианты
- Публичное чтение профиля.
- Обновлять может только владелец (subject.id == user_id) — проверка в роутере обязательна.

5) Слои
- Бизнес‑логика в сервисе, доступ и оркестрация — в роутере.
- `application` не импортирует `infrastructure` напрямую в типах исполнения.

6) Тесты
- Юнит: сервис и политики, happy/deny кейсы.
- Контракт: `ProfileOut`/`ProfileUpdate` shape; мокнуть outbox и проверить вызов паблишера.

7) Стандарты
- `from __future__ import annotations`, mypy‑strict, ruff ok.
- Коммиты: `feat(domain-profile): ...`.

Формат ответа агента:
<PLAN> кратко о шагах и рисках </PLAN>
<TESTS> перечень тестов и что покрывают </TESTS>
<CODE> изменения с пояснениями важных решений </CODE>
<SELF-REVIEW> чек‑лист линтеров/типов/контрактов/событий </SELF-REVIEW>

