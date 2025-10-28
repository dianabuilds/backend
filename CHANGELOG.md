# Changelog

## 2025-10-07

- API Gateway возвращён внутрь каталога apps/backend/app/api_gateway, обновлены импорты и документация.
- Приложения доменов переведены на команды/запросы с typed presenters — временные `UseCaseResult` удалены.
- Добавлены локальные stubs и обновлённая конфигурация mypy (строгий режим для notifications/moderation, исключения для `slugify`).
- Приведены SQL/Redis адаптеры к строгим возвращаемым типам, обновлены unit и integration тесты.
- Обновлена документация (`apps/backend/ARCHITECTURE.md`, `docs/reference/feature-flags-sql.md`) и добавлены итоговые записи о миграции фич-флагов.

## 2025-10-28
- Биллинг: публикуем событие `billing.plan.changed.v1`, добавлены уведомления пользователям и finance_ops, аудит платежей и метрики.

- Разделены публичные и административные профайл-роуты (`/v1/profile/**`, `/v1/admin/profile/**`), подключены к соответствующим контурам FastAPI.
- Добавлены интеграционные тесты профиля (`tests/integration/test_profile_routes.py`) и уточнены contour-тесты.
- Обновлена документация по профилю (`docs/features/profile-settings/README.md`, `docs/README.md`), backlog помечен выполненным.
