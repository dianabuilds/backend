from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class AISettingsOut(BaseModel):
    provider: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    # Ключ не возвращаем по соображениям безопасности
    has_api_key: bool = False


class AISettingsIn(BaseModel):
    provider: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    # При передаче None — не изменять, пустая строка "" — очистить, строка — сохранить
    api_key: Optional[str] = None
