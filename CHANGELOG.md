# Changelog

## 2025-10-07

- Перенесён API Gateway в пакет `app/api_gateway`, обновлены импорты и документация.
- Приложения доменов переведены на команды/запросы с typed presenters — временные `UseCaseResult` удалены.
- Добавлены локальные stubs и обновлённая конфигурация mypy (строгий режим для notifications/moderation, исключения для `slugify`).
- Приведены SQL/Redis адаптеры к строгим возвращаемым типам, обновлены unit и integration тесты.
- Обновлена документация (`apps/backend/ARCHITECTURE.md`, `docs/feature_flags_sql_plan.md`) и добавлены итоговые записи о миграции фич-флагов.
