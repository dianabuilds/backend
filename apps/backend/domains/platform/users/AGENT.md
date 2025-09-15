# AGENT — Users

Где править:
- Модель: `domain/models.py` (`User` — базовые публичные поля)
- Порт: `ports.py` (`UsersRepo` — get_by_id/email/wallet)
- Адаптер: `adapters/repos_sql.py` (чтение из таблицы `users`)
- Сервис: `application/service.py` (`UsersService`, `ROLE_ORDER`)
- API: `api/http.py` (`GET /v1/users/me`)
- DI: `wires.py` (`UsersContainer`)

Правила:
- Роли: иерархия `user < support < moderator < admin`. Хелпер `require_role_db(min_role)` доступен в `platform/iam/security.py`.
- Guard’ы: `require_admin` сначала проверяет JWT claim/ключ, затем при наличии контейнера сверяет роль из БД.
- Отношение к IAM: Users — источник истины для ролей. JWT может включать роль для скорости, но критичные ручки можно перепроверить по БД.

