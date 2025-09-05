# Code Validator

Валидация репозитория выполняется скриптом `scripts/validate_repo.py`.

## Запуск

```bash
python scripts/validate_repo.py
```

## Красные условия

- `ruff` обнаруживает ошибки
- `mypy` завершается с кодом ≠ 0
- `bandit` сообщает уязвимости
- `vulture` находит мёртвый код
- `pip-audit` выявляет проблемы в зависимостях
- `cyclonedx-bom` не может собрать SBOM
- health bench возвращает ошибки или успех < 100 %

Любое из условий делает проверку красной и скрипт завершится кодом 1.

## Формат отчёта

Скрипт создаёт `reports/validate_repo.md` со структурой:

```
# Repository Validation Report

## <шаг>
Command: `<команда>`

<вывод инструмента в кодовом блоке>
```

