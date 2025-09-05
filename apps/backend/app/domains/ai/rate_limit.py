from __future__ import annotations

import os
from datetime import datetime

from app.providers.cache import cache as shared_cache

# Рантайм-оверрайды лимитов (в оперативной памяти процесса)
_provider_limits_override: dict[str, int] = {}
_model_limits_override: dict[str, int] = {}


def set_provider_limit(provider: str, rpm: int | None) -> None:
    """Установить лимит RPM для провайдера (None — удалить оверрайд)."""
    key = (provider or "").strip().lower()
    if not key:
        return
    if rpm is None:
        _provider_limits_override.pop(key, None)
    else:
        _provider_limits_override[key] = max(1, int(rpm))


def set_model_limit(model: str, rpm: int | None) -> None:
    """Установить лимит RPM для модели (None — удалить оверрайд)."""
    key = (model or "").strip().lower()
    if not key:
        return
    if rpm is None:
        _model_limits_override.pop(key, None)
    else:
        _model_limits_override[key] = max(1, int(rpm))


def set_limits_from_dict(payload: dict) -> None:
    """Массовая установка лимитов из словаря.

    Формат: {"providers": {slug: rpm}, "models": {name: rpm}}.
    """
    provs = payload.get("providers") or {}
    mods = payload.get("models") or {}
    if isinstance(provs, dict):
        for k, v in provs.items():
            try:
                set_provider_limit(str(k), None if v in (None, "", 0) else int(v))
            except Exception:
                continue
    if isinstance(mods, dict):
        for k, v in mods.items():
            try:
                set_model_limit(str(k), None if v in (None, "", 0) else int(v))
            except Exception:
                continue


def get_limits_snapshot() -> dict:
    return {
        "providers": dict(_provider_limits_override),
        "models": dict(_model_limits_override),
    }


def _window_key_provider(provider: str) -> str:
    now = datetime.utcnow()
    bucket = now.strftime("%Y%m%d%H%M")  # поминутное окно
    return f"rl:llm:prov:{provider}:{bucket}"


def _window_key_model(provider: str, model: str) -> str:
    now = datetime.utcnow()
    bucket = now.strftime("%Y%m%d%H%M")
    # нормализуем модель для ключа
    m = (model or "").replace("/", "_").replace(":", "_")
    return f"rl:llm:model:{provider}:{m}:{bucket}"


def _ttl_seconds() -> int:
    # немного больше минуты, чтобы окно успело закрыться
    return 90


def _limit_for_provider(provider: str) -> int:
    # Сначала берём рантайм-оверрайд
    key = (provider or "").strip().lower()
    if key in _provider_limits_override:
        return max(1, int(_provider_limits_override[key]))
    # Затем ENV: AI_RATE_OPENAI_RPM / AI_RATE_ANTHROPIC_RPM / AI_RATE_DEFAULT_RPM
    env_key = f"AI_RATE_{(provider or '').upper()}_RPM"
    try:
        v = int(os.getenv(env_key) or "")
        if v > 0:
            return v
    except Exception:
        pass
    try:
        v = int(os.getenv("AI_RATE_DEFAULT_RPM", "60"))
        return max(1, v)
    except Exception:
        return 60


def _limit_for_model(model: str) -> int | None:
    # Сначала рантайм-оверрайд
    key = (model or "").strip().lower()
    if key in _model_limits_override:
        return max(1, int(_model_limits_override[key]))
    # Затем ENV: AI_RATE_MODEL_{MODEL}_RPM
    key_env = (
        (model or "")
        .upper()
        .replace("/", "_")
        .replace(":", "_")
        .replace(".", "_")
        .replace("-", "_")
    )
    env_key = f"AI_RATE_MODEL_{key_env}_RPM"
    try:
        v = int(os.getenv(env_key) or "")
        if v > 0:
            return v
    except Exception:
        pass
    return None  # нет явного лимита для этой модели


async def _incr_with_ttl(key: str, amount: int, limit: int) -> bool:
    current = await shared_cache.incr(key, amount)
    if current == amount:
        await shared_cache.expire(key, _ttl_seconds())
    if current > limit:
        await shared_cache.incr(key, -amount)
        return False
    return True


async def try_acquire(provider: str, *, amount: int = 1) -> bool:
    key = _window_key_provider(provider)
    limit = _limit_for_provider(provider)
    return await _incr_with_ttl(key, amount, limit)


async def try_acquire_model(provider: str, model: str, *, amount: int = 1) -> bool | None:
    limit = _limit_for_model(model)
    if limit is None:
        return None
    key = _window_key_model(provider, model)
    ok = await _incr_with_ttl(key, amount, limit)
    return ok


async def try_acquire_for(provider: str, model: str, *, amount: int = 1) -> tuple[bool, str | None]:
    m = await try_acquire_model(provider, model, amount=amount)
    if m is False:
        return False, "model"
    p = await try_acquire(provider, amount=amount)
    if not p:
        return False, "provider"
    return True, None
