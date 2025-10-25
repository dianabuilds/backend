# Code Validator

Валидация репозитория выполняется скриптом `scripts/validate_repo.py`.

## Запуск

```bash
python scripts/validate_repo.py
```

## Проверки

Скрипт последовательно выполняет следующие шаги:

- `ruff`: запуск `python -m ruff check . --config pyproject.toml` в каталоге `apps/backend`.
- `mypy`: запуск `python -m mypy --config-file mypy.ini apps/backend`.
- `bandit`: запуск `python -m bandit -q -r apps/backend/app apps/backend/domains apps/backend/packages apps/backend/workers scripts health -x apps/backend/.venv,apps/backend/app/tests,tests`.
- `vulture`: запуск `python -m vulture apps/backend/app apps/backend/domains apps/backend/packages apps/backend/workers apps/backend/scripts tests health scripts --min-confidence 80 --exclude apps/backend/.venv`.
- `pip-audit`: запуск `python -m pip_audit --requirement apps/backend/requirements.txt --requirement tests/requirements-test.txt`.
- `cyclonedx`: генерация SBOM `python -m cyclonedx_py requirements apps/backend/requirements.txt --of JSON -o var/sbom.json`.
- `health bench`: локальная команда `python -m health bench`, проверяющая наличие health-эндпоинтов и smoke-тестов.

Если какой-либо инструмент завершился ненулевым кодом, `validate_repo.py` возвращает код 1.

## Отчёт

- Отчёт `reports/validate_repo.md` содержит отдельную секцию по каждой проверке: название, команду, код завершения, статус (success/failure) и полный вывод в блоке кода.
- Во время шага CycloneDX создаётся `var/sbom.json`.

## Требования

- Python 3.11+.
- Установленные пакеты: `ruff`, `mypy`, `bandit`, `vulture`, `pip-audit`, `cyclonedx-bom` (добавляет CLI `cyclonedx-py`).
- Для `health bench` используется модуль `health` из репозитория.

## Примечания по безопасности

- Bandit ожидает явные логи вместо `except: pass`; соответствующие обработчики добавлены в пакетах `packages/core` и `workers` для traceability.
- Джиттер периодических воркеров вычисляется через `secrets.SystemRandom`, что исключает предупреждение B311 о псевдослучайных генераторах.
- Для валидации If-Match используется константа `WILDCARD_ETAG` с пометкой `# nosec B105`, а импорт `subprocess` снабжён пояснениями по предупреждениям B404/B603.

## GitHub Actions

- Workflow `.github/workflows/ci.yml` состоит из джобов `backend-quality`, `backend-contour-smoke`, `frontend-quality`. Матрица `contour: [public, admin, ops]` запускает smoke-тесты `tests/app/api_gateway/test_contours.py` с переменной окружения `APP_API_CONTOUR`.
- Для каждого контура сохраняются артефакты `pytest-<contour>.xml` и `pytest-<contour>.log`, которые прикладываются к результатам Actions для разбора падений.
- Джоб `backend-contour-smoke` работает с параметром `fail-fast: false`, поэтому сбой одного контура не прерывает проверки остальных.
