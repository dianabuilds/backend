#!/usr/bin/env python
"""
Скрипт для инициализации базы данных.
Создает начальную миграцию и применяет её.
"""
import os
import subprocess
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

ALEMBIC_CONFIG = project_root / "apps" / "backend" / "alembic.ini"

# Импортируем настройки приложения
from apps.backend.app.core.config import settings


def run_command(command: list[str], error_message: str) -> bool:
    """Выполняет команду в терминале."""
    try:
        print(f"Running: {' '.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"{error_message}: {e.stderr}")
        return False


def main() -> bool:
    """Основная функция для инициализации базы данных."""
    print(f"Initializing database for environment: {settings.environment}")

    # Проверяем, существует ли директория alembic/versions
    versions_dir = project_root / "apps" / "backend" / "alembic" / "versions"
    if not versions_dir.exists():
        os.makedirs(versions_dir, exist_ok=True)
        print(f"Created versions directory: {versions_dir}")

    # Проверяем, есть ли уже миграции
    has_migrations = any(versions_dir.glob("*.py"))

    if not has_migrations:
        # Создаем начальную миграцию
        if not run_command(
            [
                "alembic",
                "-c",
                str(ALEMBIC_CONFIG),
                "revision",
                "--autogenerate",
                "-m",
                "initial",
            ],
            "Failed to create initial migration",
        ):
            return False

    # Применяем миграции
    if not run_command(
        ["alembic", "-c", str(ALEMBIC_CONFIG), "upgrade", "head"],
        "Failed to apply migrations",
    ):
        return False

    print("Database initialization completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
