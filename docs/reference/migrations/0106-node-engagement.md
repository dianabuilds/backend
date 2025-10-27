# Миграция 0106_node_engagement

## Что меняем
- В таблицу `nodes` добавляем колонки: `views_count`, `reactions_like_count`, `comments_disabled`, `comments_locked_by`, `comments_locked_at`.
- Создаём `node_views_daily` для агрегирования просмотров по дням.
- Создаём `node_reactions` с уникальным ограничением `(node_id, user_id, reaction_type)`.
- Создаём `node_comments` (дерево комментариев, глубина ≤ 5) со статусами и индексами по `node_id`, `parent_comment_id`, `author_id`.
- Создаём `node_comment_bans` для локальных банов.
- Добавляем индексы: `ix_nodes_views_count`, `ix_nodes_reactions_like_count`, `ix_nodes_comments_disabled`, а также необходимые индексы на новых таблицах.

## Перед применением
1. Убедиться, что расширение `pgcrypto` включено, а при необходимости `pgvector` зарегистрирован.
2. Проверить свободное место в БД — таблицы engagement растут быстро.
3. Сделать бэкап (snapshot или `pg_dump`) перед обновлением production.

## Применение
```bash
poetry run alembic upgrade head
```

### Откат
```bash
poetry run alembic downgrade 0105_moderator_user_notes
```

## Проверки после применения
- `SELECT column_name FROM information_schema.columns WHERE table_name = 'nodes' AND column_name IN ('views_count','reactions_like_count','comments_disabled');`
- `SELECT count(*) FROM node_comments;` — убеждаемся, что таблица создана.
- `\d+ node_reactions` — проверяем индексы в psql.

## Эксплуатационные заметки
- Бэкфил не выполняется: счётчики стартуют с нуля. При необходимости готовим разовый скрипт для восстановления исторических данных.
- Ограничение частоты просмотров опирается на конфигурацию Redis (`apps/backend/app/api_gateway/wires.py`, ежедневный TTL).

## Статус
- 2025-10-03: миграция применена, smoke-проверки прошли успешно.
