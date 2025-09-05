from __future__ import annotations

import os
from typing import Any

from app.domains.ai.application.ports.settings_repo import IAISettingsRepository

# ENV дефолты
ENV_PROVIDER = os.getenv("AI_PROVIDER")
ENV_BASE_URL = os.getenv("AI_BASE_URL")
ENV_MODEL = os.getenv("AI_MODEL")
ENV_CB_FAIL_RATE = os.getenv("AI_CB_FAIL_RATE_THRESHOLD")
ENV_CB_MIN_REQUESTS = os.getenv("AI_CB_MIN_REQUESTS")
ENV_CB_OPEN_SECONDS = os.getenv("AI_CB_OPEN_SECONDS")


def _env_cb_defaults() -> dict[str, Any]:
    fail_rate = float(ENV_CB_FAIL_RATE) if ENV_CB_FAIL_RATE else 0.5
    min_reqs = int(ENV_CB_MIN_REQUESTS) if ENV_CB_MIN_REQUESTS else 20
    open_sec = int(ENV_CB_OPEN_SECONDS) if ENV_CB_OPEN_SECONDS else 60
    return {
        "fail_rate_threshold": fail_rate,
        "min_requests": min_reqs,
        "open_seconds": open_sec,
    }


class SettingsService:
    def __init__(self, repo: IAISettingsRepository) -> None:
        self._repo = repo

    async def get_ai_settings(self) -> dict[str, Any]:
        defaults = {
            "provider": ENV_PROVIDER,
            "base_url": ENV_BASE_URL,
            "model": ENV_MODEL,
            "model_map": None,
            "cb": _env_cb_defaults(),
            "has_api_key": False,
            "api_key": None,
        }
        row = await self._repo.get_singleton(create_if_missing=True, defaults=defaults)
        data = row.as_public_dict()

        # Fallback на ENV, если в БД не заполнено
        if not data.get("provider") and ENV_PROVIDER:
            data["provider"] = ENV_PROVIDER
        if not data.get("base_url") and ENV_BASE_URL:
            data["base_url"] = ENV_BASE_URL
        if (not data.get("model")) and ENV_MODEL:
            data["model"] = ENV_MODEL
        cb = data.get("cb") or {}
        env_cb = _env_cb_defaults()
        for k, v in env_cb.items():
            cb.setdefault(k, v)
        data["cb"] = cb

        if not isinstance(data.get("model_map"), dict):
            data["model_map"] = {}

        return data

    async def update_ai_settings(
        self,
        *,
        provider: str | None | None = None,
        base_url: str | None | None = None,
        model: str | None | None = None,
        api_key: (
            str | None | None
        ) = None,  # None — не менять, "" — очистить, строка — сохранить
        model_map: dict[str, Any] | None | None = None,
        cb: dict[str, Any] | None | None = None,
    ) -> dict[str, Any]:
        # Загружаем строку (создаём при необходимости)
        row = await self._repo.get_singleton(
            create_if_missing=True,
            defaults={
                "provider": ENV_PROVIDER,
                "base_url": ENV_BASE_URL,
                "model": ENV_MODEL,
                "model_map": None,
                "cb": _env_cb_defaults(),
                "has_api_key": False,
                "api_key": None,
            },
        )

        row.provider = provider
        row.base_url = base_url
        row.model = model

        if model_map is not None:
            row.model_map = model_map if isinstance(model_map, dict) else None

        if cb is not None:
            normalized_cb = {
                "fail_rate_threshold": float(
                    cb.get(
                        "fail_rate_threshold", _env_cb_defaults()["fail_rate_threshold"]
                    )
                ),
                "min_requests": int(
                    cb.get("min_requests", _env_cb_defaults()["min_requests"])
                ),
                "open_seconds": int(
                    cb.get("open_seconds", _env_cb_defaults()["open_seconds"])
                ),
            }
            row.cb = normalized_cb

        if api_key is not None:
            if api_key == "":
                row.api_key = None
                row.has_api_key = False
            else:
                row.api_key = api_key
                row.has_api_key = True

        await self._repo.flush(row)
        return await self.get_ai_settings()

    @staticmethod
    def choose_stage_model(settings: dict[str, Any], stage: str) -> dict[str, Any]:
        """
        Возвращает конфиг модели для заданной стадии:
        1) Если в model_map есть ключ stage — берём его
           (provider/base_url/model/параметры).
        2) Иначе используем дефолты provider/base_url/model.
        """
        model_map = settings.get("model_map") or {}
        if stage in model_map and isinstance(model_map[stage], dict):
            base = {
                "provider": settings.get("provider"),
                "base_url": settings.get("base_url"),
                "model": settings.get("model"),
            }
            base.update({k: v for k, v in model_map[stage].items() if v is not None})
            return base
        return {
            "provider": settings.get("provider"),
            "base_url": settings.get("base_url"),
            "model": settings.get("model"),
        }
