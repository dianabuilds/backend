# Wave 2 — Бэкенд

## Снимок importlinter — 11.10.2025
- Команда: `python -m importlinter.cli lint --config apps/backend/importlinter.ini`.
- Конфигурация: добавлены контракты `layers_product_worlds`, `layers_product_ai`, `layers_product_premium` для новых доменов `apps.backend.domains.product`.
- Результат: нарушений не обнаружено (exit code 0).
- Отчёт: `var/backend-import-lint.txt`.

## Наблюдения и следующие шаги
- `product/ai` и `product/premium` используют упрощённую слойность (`api -> application`/`adapters`), поэтому отдельные контракты зафиксированы до расширения доменных слоёв.
- Для `product/content`, `product/navigation`, `product/quests` и других доменов с инфраструктурой требуется выровнять структуру каталогов, после чего можно объединить контракты через `containers`.
- Дальнейшие проверки: добавить forbidden-правила между доменами после ревизии сервисных фасадов и событийной шины.
