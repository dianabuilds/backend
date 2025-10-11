# ADR 2025-10-11 Wave-0 Quality Baseline

## Контекст
- Wave-0 закрыла подготовительные задачи: восстановлен `scripts/validate_repo.py`, собрана карта зависимостей, снят importlinter snapshot, собраны baseline Lighthouse/coverage/API и подтверждены KPI.
- Метрики и ответственные закреплены в `docs/code-audit-plan-2025.md#критерии-качества-и-метрики`.
- Получены артефакты: `var/lighthouse-*.json`, `var/frontend-bundle.json`, `var/backend-import-lint.txt`, `var/api-benchmarks.json`, `reports/validate_repo.md`.

## Решение
1. Поддерживать единый backlog качества в `docs/code-audit-plan-2025.md#wave-0-—-backlog-качества` с форматом «модуль > проблема > метрика/лог > предложение > приоритет».
2. Для фронтенда зафиксировать baseline и чек-лист Wave-1 в `apps/web/frontend-audit.md`, обновлять показатели еженедельно и публиковать их в Slack #web-platform.
3. Для бэкенда вести аналогичный чек-лист в `docs/backend-testing-strategy.md`, приоритизируя подъём покрытия до ≥85% и устранение Bandit-алертов.
4. Использовать baseline артефакты Wave-0 как вход для планирования Wave-1 (performance, bundle size, coverage, API smoke).

## Последствия
- Сформирован единый список первоочередных задач качества, связанный с измерениями.
- Команды фронтенда и бэкенда получили явные чек-листы на старт Wave-1.
- Регулярные замеры Lighthouse и coverage становятся обязательным пунктом еженедельной отчётности.

## Следующие шаги
- Закрыть backlog-элементы с приоритетом P0–P1 до начала Wave-1.
- Включить обновление артефактов (`var/*`, `reports/validate_repo.md`) в nightly pipeline и фиксировать регрессии.
- Подготовить отдельные ADR по фронтенд-слоям и доменным границам после выполнения Wave-1/Wave-2.
