import os
import json
from pathlib import Path
from typing import Optional


def _parse_line(line: str) -> Optional[tuple[str, str]]:
    # Удаляем комментарии и пробелы
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    if s.startswith("export "):
        s = s[len("export ") :].lstrip()

    if "=" not in s:
        return None

    key, value = s.split("=", 1)
    key = key.strip()
    value = value.strip()

    # Убираем кавычки, если есть
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1]

    return key, value


def _load_file(path: Path, override: bool) -> bool:
    loaded = False
    try:
        with path.open("r", encoding="utf-8") as f:
            for raw in f:
                parsed = _parse_line(raw)
                if not parsed:
                    continue
                key, value = parsed
                if not override and key in os.environ:
                    continue
                os.environ[key] = value
        loaded = True
    except FileNotFoundError:
        loaded = False
    return loaded


def _looks_like_json(value: str) -> bool:
    s = value.strip()
    return s.startswith("[") or s.startswith("{") or (
        s.startswith('"') and s.endswith('"')
    )


def _normalize_env_for_pydantic_json() -> None:
    """
    Преобразует значения, ожидаемые как JSON-массивы, если они заданы как простые строки/CSV.
    Это нужно для pydantic-settings, который парсит списковые поля через json.loads.
    """
    list_keys = {
        # Вложенная форма с двойным подчёркиванием (env_nested_delimiter="__")
        "CORS__ALLOWED_ORIGINS",
        "CORS__ALLOWED_METHODS",
        "CORS__ALLOWED_HEADERS",
        # Плоская форма с префиксом из под-настроек (env_prefix="CORS_")
        "CORS_ALLOWED_ORIGINS",
        "CORS_ALLOWED_METHODS",
        "CORS_ALLOWED_HEADERS",
    }
    for key in list_keys:
        val = os.environ.get(key)
        if val is None:
            continue
        if _looks_like_json(val):
            continue
        # Разделяем по запятой или точке с запятой
        parts = [p.strip() for p in val.replace(";", ",").split(",") if p.strip()]
        os.environ[key] = json.dumps(parts if parts else [])


def load_dotenv(path: Optional[str | Path] = None, override: bool = False) -> Optional[Path]:
    """
    Загружает переменные окружения из .env в os.environ.
    - path: явный путь к .env; если не указан — ищем по типовым локациям.
    - override: перезаписывать ли уже существующие переменные окружения.
    Возвращает путь к загруженному .env или None, если ничего не найдено.
    """
    candidates: list[Path] = []

    if path:
        p = Path(path)
        if p.exists():
            candidates.append(p)
    else:
        # Текущая директория выполнения
        candidates.append(Path.cwd() / ".env")
        # Корень проекта (на 2 уровня выше этого файла — app/core/ -> /)
        try:
            candidates.append(Path(__file__).resolve().parents[2] / ".env")
        except IndexError:
            pass
        # Папка приложения
        candidates.append(Path(__file__).resolve().parents[1] / ".env")

        # Локальные варианты, если есть
        candidates.append(Path.cwd() / ".env.local")

    for candidate in candidates:
        if candidate.exists() and _load_file(candidate, override=override):
            # После успешной загрузки нормализуем значения, которые должны быть JSON
            _normalize_env_for_pydantic_json()
            return candidate

    # Даже если .env не найден, нормализуем переменные окружения, заданные извне
    _normalize_env_for_pydantic_json()
    return None
