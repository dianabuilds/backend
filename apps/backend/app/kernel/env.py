from __future__ import annotations

import json
import os
from pathlib import Path


def _parse_line(line: str) -> tuple[str, str] | None:
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
    return s.startswith("[") or s.startswith("{") or (s.startswith('"') and s.endswith('"'))


def _normalize_env_for_pydantic_json() -> None:
    list_keys = {
        "APP_CORS_ALLOW_ORIGINS",
        "APP_CORS_ALLOW_METHODS",
        "APP_CORS_ALLOW_HEADERS",
        "CORS_ALLOW_ORIGINS",
        "CORS_ALLOW_METHODS",
        "CORS_ALLOW_HEADERS",
        "CORS_ALLOWED_ORIGINS",
        "CORS_ALLOWED_METHODS",
        "CORS_ALLOWED_HEADERS",
    }
    normalized_keys = {k.lower() for k in list_keys}
    for key, val in list(os.environ.items()):
        if key.lower() not in normalized_keys:
            continue
        if val is None or _looks_like_json(val):
            continue
        parts = [p.strip() for p in val.replace(";", ",").split(",") if p.strip()]
        os.environ[key] = json.dumps(parts if parts else [])


def load_dotenv(path: str | Path | None = None, override: bool = False) -> Path | None:
    candidates: list[Path] = []
    if path:
        p = Path(path)
        if p.exists():
            candidates.append(p)
    else:
        cwd = Path.cwd()
        candidates.append(cwd / ".env")
        candidates.append(cwd / ".env.local")
        file_path = Path(__file__).resolve()
        for parent in file_path.parents:
            candidates.append(parent / ".env")
            candidates.append(parent / ".env.local")
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists() and _load_file(candidate, override=override):
            _normalize_env_for_pydantic_json()
            return candidate
    _normalize_env_for_pydantic_json()
    return None


__all__ = ["load_dotenv"]

