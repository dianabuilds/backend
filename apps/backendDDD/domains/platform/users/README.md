# Platform Users

Базовый платформенный домен пользователей для чтения публичных данных и ролей.

- Модель: `domain/models.py` (`User`)
- Порт: `ports.py` (`UsersRepo` — get_by_id/email/wallet)
- Адаптер: `adapters/repos_sql.py` (таблица `users`)
- Сервис: `application/service.py` (`UsersService`, `ROLE_ORDER`)
- API: `api/http.py` — `GET /v1/users/me`
- DI: `wires.py`

## Использование с IAM
- `require_admin` в `platform/iam/security.py` при необходимости сверяет роль по БД через `UsersService`.
- Доступен хелпер `require_role_db(min_role)`, если нужно требовать роль ниже admin.

## TODO
- Расширить API (admin): `GET /v1/users/{id}` (guard), фильтры/пагинация.
- Кеширование чтений (Redis) и инвалидация на изменения профиля.
- Обогащение JWT при login/refresh данными роли (cохранить проверку БД для критичных ручек).

