from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class LLMProviderCfg:
    slug: str
    title: str | None = None
    enabled: bool = True
    base_url: str | None = None
    api_key: str | None = None
    timeout_sec: int | None = None
    extras: dict[str, Any] | None = None


@dataclass(slots=True)
class LLMModelCfg:
    id: str
    name: str
    provider_slug: str
    version: str | None = None
    status: str = "active"  # active/disabled
    is_default: bool = False
    params: dict[str, Any] | None = None


@dataclass(slots=True)
class FallbackRule:
    id: str
    primary_model: str
    fallback_model: str
    mode: str = "on_error"  # on_error, ratio
    ratio: int | None = None  # 0..100 if mode==ratio


class LLMRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, LLMProviderCfg] = {}
        self._models: dict[str, LLMModelCfg] = {}
        self._fallbacks: dict[str, FallbackRule] = {}

    # Providers
    async def list_providers(self) -> list[LLMProviderCfg]:
        return list(self._providers.values())

    async def upsert_provider(self, data: dict[str, Any]) -> LLMProviderCfg:
        slug = str(data.get("slug") or "").strip()
        if not slug:
            raise ValueError("slug_required")
        cfg = LLMProviderCfg(
            slug=slug,
            title=str(data.get("title") or "") or None,
            enabled=bool(data.get("enabled", True)),
            base_url=str(data.get("base_url") or "") or None,
            api_key=str(data.get("api_key") or "") or None,
            timeout_sec=int(data.get("timeout_sec") or 0) or None,
            extras=dict(data.get("extras") or {}) or None,
        )
        self._providers[slug] = cfg
        return cfg

    async def delete_provider(self, slug: str) -> None:
        self._providers.pop(slug, None)

    # Models
    async def list_models(self) -> list[LLMModelCfg]:
        return list(self._models.values())

    async def upsert_model(self, data: dict[str, Any]) -> LLMModelCfg:
        mid = str(data.get("id") or uuid.uuid4())
        name = str(data.get("name") or "").strip()
        provider_slug = str(data.get("provider_slug") or "").strip()
        if not name or not provider_slug:
            raise ValueError("name_and_provider_required")
        cfg = LLMModelCfg(
            id=mid,
            name=name,
            provider_slug=provider_slug,
            version=str(data.get("version") or "") or None,
            status=str(data.get("status") or "active"),
            is_default=bool(data.get("is_default", False)),
            params=dict(data.get("params") or {}) or None,
        )
        self._models[mid] = cfg
        return cfg

    async def delete_model(self, model_id: str) -> None:
        self._models.pop(model_id, None)

    # Fallbacks
    async def list_fallbacks(self) -> list[FallbackRule]:
        return list(self._fallbacks.values())

    async def upsert_fallback(self, data: dict[str, Any]) -> FallbackRule:
        rid = str(data.get("id") or uuid.uuid4())
        primary = str(data.get("primary_model") or "").strip()
        fallback = str(data.get("fallback_model") or "").strip()
        if not primary or not fallback:
            raise ValueError("primary_and_fallback_required")
        mode = str(data.get("mode") or "on_error")
        ratio_val = data.get("ratio")
        ratio: int | None = int(ratio_val) if ratio_val is not None else None
        rule = FallbackRule(
            id=rid,
            primary_model=primary,
            fallback_model=fallback,
            mode=mode,
            ratio=ratio,
        )
        self._fallbacks[rid] = rule
        return rule

    async def delete_fallback(self, rule_id: str) -> None:
        self._fallbacks.pop(rule_id, None)


def redact_provider(d: LLMProviderCfg) -> dict[str, Any]:
    out = asdict(d)
    if out.get("api_key"):
        out["api_key"] = "***"
    return out


__all__ = [
    "LLMProviderCfg",
    "LLMModelCfg",
    "FallbackRule",
    "LLMRegistry",
    "redact_provider",
]
