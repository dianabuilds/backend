from __future__ import annotations

from pydantic import BaseModel


class AISettingsOut(BaseModel):
    provider: str | None = None
    base_url: str | None = None
    model: str | None = None
    # Ключ не возвращаем по соображениям безопасности
    has_api_key: bool = False


class AISettingsIn(BaseModel):
    provider: str | None = None
    base_url: str | None = None
    model: str | None = None
    # При передаче None — не изменять, пустая строка "" — очистить, строка — сохранить
    api_key: str | None = None
