from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Protocol

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from packages.core.config import sanitize_async_dsn
from packages.core.db import get_async_engine


@dataclass(slots=True)
class LLMProviderCfg:
    slug: str
    title: str | None = None
    enabled: bool = True
    base_url: str | None = None
    api_key: str | None = None
    timeout_sec: int | None = None
    extras: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class LLMModelCfg:
    id: str
    name: str
    provider_slug: str
    version: str | None = None
    status: str = "active"  # active/disabled
    is_default: bool = False
    params: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class FallbackRule:
    id: str
    primary_model: str
    fallback_model: str
    mode: str = "on_error"  # on_error, ratio
    ratio: int | None = None  # 0..100 if mode==ratio
    priority: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class _RegistryBackend(Protocol):
    async def list_providers(self) -> list[LLMProviderCfg]: ...

    async def upsert_provider(self, data: dict[str, Any]) -> LLMProviderCfg: ...

    async def delete_provider(self, slug: str) -> None: ...

    async def list_models(self) -> list[LLMModelCfg]: ...

    async def upsert_model(self, data: dict[str, Any]) -> LLMModelCfg: ...

    async def delete_model(self, model_id: str) -> None: ...

    async def list_fallbacks(self) -> list[FallbackRule]: ...

    async def upsert_fallback(self, data: dict[str, Any]) -> FallbackRule: ...

    async def delete_fallback(self, rule_id: str) -> None: ...


class LLMRegistry:
    def __init__(self, engine: AsyncEngine | str | None = None) -> None:
        if engine is None:
            self._backend: _RegistryBackend = _MemoryBackend()
        else:
            self._backend = _SQLBackend(engine)

    # Providers
    async def list_providers(self) -> list[LLMProviderCfg]:
        return await self._backend.list_providers()

    async def upsert_provider(self, data: dict[str, Any]) -> LLMProviderCfg:
        return await self._backend.upsert_provider(data)

    async def delete_provider(self, slug: str) -> None:
        await self._backend.delete_provider(slug)

    # Models
    async def list_models(self) -> list[LLMModelCfg]:
        return await self._backend.list_models()

    async def upsert_model(self, data: dict[str, Any]) -> LLMModelCfg:
        return await self._backend.upsert_model(data)

    async def delete_model(self, model_id: str) -> None:
        await self._backend.delete_model(model_id)

    # Fallbacks
    async def list_fallbacks(self) -> list[FallbackRule]:
        return await self._backend.list_fallbacks()

    async def upsert_fallback(self, data: dict[str, Any]) -> FallbackRule:
        return await self._backend.upsert_fallback(data)

    async def delete_fallback(self, rule_id: str) -> None:
        await self._backend.delete_fallback(rule_id)


class _MemoryBackend:
    def __init__(self) -> None:
        self._providers: dict[str, LLMProviderCfg] = {}
        self._models: dict[str, LLMModelCfg] = {}
        self._fallbacks: dict[str, FallbackRule] = {}

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
        priority_val = data.get("priority")
        priority: int | None = int(priority_val) if priority_val is not None else None
        rule = FallbackRule(
            id=rid,
            primary_model=primary,
            fallback_model=fallback,
            mode=mode,
            ratio=ratio,
            priority=priority,
        )
        self._fallbacks[rid] = rule
        return rule

    async def delete_fallback(self, rule_id: str) -> None:
        self._fallbacks.pop(rule_id, None)


class _SQLBackend:
    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, str):
            self._engine: AsyncEngine | None = None
            self._dsn: str | None = sanitize_async_dsn(engine)
        else:
            self._engine = engine
            self._dsn = None

    async def list_providers(self) -> list[LLMProviderCfg]:
        sql = text(
            """
            SELECT slug,
                   title,
                   enabled,
                   base_url,
                   api_key,
                   timeout_sec,
                   extras,
                   created_at,
                   updated_at
              FROM ai_providers
             ORDER BY slug
            """
        )
        engine, dispose = await self._engine_for_call()
        try:
            async with engine.begin() as conn:
                rows = (await conn.execute(sql)).mappings().all()
            result: list[LLMProviderCfg] = []
            for row in rows:
                extras = row["extras"] if row["extras"] is None else dict(row["extras"])
                result.append(
                    LLMProviderCfg(
                        slug=row["slug"],
                        title=row["title"],
                        enabled=bool(row["enabled"]),
                        base_url=row["base_url"],
                        api_key=row["api_key"],
                        timeout_sec=row["timeout_sec"],
                        extras=extras,
                        created_at=row.get("created_at"),
                        updated_at=row.get("updated_at"),
                    )
                )
            return result
        finally:
            if dispose:
                await engine.dispose()

    async def upsert_provider(self, data: dict[str, Any]) -> LLMProviderCfg:
        slug = str(data.get("slug") or "").strip()
        if not slug:
            raise ValueError("slug_required")
        sql = text(
            """
            INSERT INTO ai_providers (slug, title, enabled, base_url, api_key, timeout_sec, extras)
            VALUES (:slug, :title, :enabled, :base_url, :api_key, :timeout_sec, CAST(:extras AS jsonb))
            ON CONFLICT (slug) DO UPDATE SET
              title = EXCLUDED.title,
              enabled = EXCLUDED.enabled,
              base_url = EXCLUDED.base_url,
              api_key = EXCLUDED.api_key,
              timeout_sec = EXCLUDED.timeout_sec,
              extras = EXCLUDED.extras,
              updated_at = now()
            RETURNING slug, title, enabled, base_url, api_key, timeout_sec, extras, created_at, updated_at
            """
        )
        extras = dict(data.get("extras") or {}) or None
        params = {
            "slug": slug,
            "title": str(data.get("title") or "") or None,
            "enabled": bool(data.get("enabled", True)),
            "base_url": str(data.get("base_url") or "") or None,
            "api_key": str(data.get("api_key") or "") or None,
            "timeout_sec": int(data.get("timeout_sec") or 0) or None,
            "extras": json.dumps(extras) if extras is not None else None,
        }
        engine, dispose = await self._engine_for_call()
        try:
            async with engine.begin() as conn:
                row = (await conn.execute(sql, params)).mappings().first()
            assert row is not None
            stored_extras = row["extras"] if row["extras"] is None else dict(row["extras"])
            return LLMProviderCfg(
                slug=row["slug"],
                title=row["title"],
                enabled=bool(row["enabled"]),
                base_url=row["base_url"],
                api_key=row["api_key"],
                timeout_sec=row["timeout_sec"],
                extras=stored_extras,
                created_at=row.get("created_at"),
                updated_at=row.get("updated_at"),
            )
        finally:
            if dispose:
                await engine.dispose()

    async def delete_provider(self, slug: str) -> None:
        sql = text("DELETE FROM ai_providers WHERE slug = :slug")
        engine, dispose = await self._engine_for_call()
        try:
            async with engine.begin() as conn:
                await conn.execute(sql, {"slug": slug})
        finally:
            if dispose:
                await engine.dispose()

    async def list_models(self) -> list[LLMModelCfg]:
        sql = text(
            """
            SELECT id::text AS id,
                   name,
                   provider_slug,
                   version,
                   status,
                   is_default,
                   params,
                   created_at,
                   updated_at
              FROM ai_models
             ORDER BY updated_at DESC, created_at DESC
            """
        )
        engine, dispose = await self._engine_for_call()
        try:
            async with engine.begin() as conn:
                rows = (await conn.execute(sql)).mappings().all()
            result: list[LLMModelCfg] = []
            for row in rows:
                params = row["params"] if row["params"] is None else dict(row["params"])
                result.append(
                    LLMModelCfg(
                        id=str(row["id"]),
                        name=row["name"],
                        provider_slug=row["provider_slug"],
                        version=row["version"],
                        status=row["status"],
                        is_default=bool(row["is_default"]),
                        params=params,
                        created_at=row.get("created_at"),
                        updated_at=row.get("updated_at"),
                    )
                )
            return result
        finally:
            if dispose:
                await engine.dispose()

    async def upsert_model(self, data: dict[str, Any]) -> LLMModelCfg:
        mid = str(data.get("id") or uuid.uuid4())
        name = str(data.get("name") or "").strip()
        provider_slug = str(data.get("provider_slug") or "").strip()
        if not name or not provider_slug:
            raise ValueError("name_and_provider_required")
        sql = text(
            """
            INSERT INTO ai_models (
                id, name, provider_slug, version, status, is_default, params
            )
            VALUES (
                cast(:id as uuid), :name, :provider_slug, :version, :status, :is_default, CAST(:params AS jsonb)
            )
            ON CONFLICT (id) DO UPDATE SET
              name = EXCLUDED.name,
              provider_slug = EXCLUDED.provider_slug,
              version = EXCLUDED.version,
              status = EXCLUDED.status,
              is_default = EXCLUDED.is_default,
              params = EXCLUDED.params,
              updated_at = now()
            RETURNING id::text AS id, name, provider_slug, version, status, is_default, params, created_at, updated_at
            """
        )
        params_json = dict(data.get("params") or {}) or None
        params = {
            "id": mid,
            "name": name,
            "provider_slug": provider_slug,
            "version": str(data.get("version") or "") or None,
            "status": str(data.get("status") or "active"),
            "is_default": bool(data.get("is_default", False)),
            "params": json.dumps(params_json) if params_json is not None else None,
        }
        engine, dispose = await self._engine_for_call()
        try:
            async with engine.begin() as conn:
                row = (await conn.execute(sql, params)).mappings().first()
            assert row is not None
            stored_params = row["params"] if row["params"] is None else dict(row["params"])
            return LLMModelCfg(
                id=str(row["id"]),
                name=row["name"],
                provider_slug=row["provider_slug"],
                version=row["version"],
                status=row["status"],
                is_default=bool(row["is_default"]),
                params=stored_params,
                created_at=row.get("created_at"),
                updated_at=row.get("updated_at"),
            )
        finally:
            if dispose:
                await engine.dispose()

    async def delete_model(self, model_id: str) -> None:
        sql = text("DELETE FROM ai_models WHERE id = cast(:id as uuid)")
        engine, dispose = await self._engine_for_call()
        try:
            async with engine.begin() as conn:
                await conn.execute(sql, {"id": model_id})
        finally:
            if dispose:
                await engine.dispose()

    async def list_fallbacks(self) -> list[FallbackRule]:
        sql = text(
            """
            SELECT id::text AS id,
                   primary_model,
                   fallback_model,
                   mode,
                   ratio,
                   priority,
                   created_at,
                   updated_at
              FROM ai_fallbacks
             ORDER BY priority NULLS LAST, created_at ASC
            """
        )
        engine, dispose = await self._engine_for_call()
        try:
            async with engine.begin() as conn:
                rows = (await conn.execute(sql)).mappings().all()
            return [
                FallbackRule(
                    id=str(row["id"]),
                    primary_model=row["primary_model"],
                    fallback_model=row["fallback_model"],
                    mode=row["mode"],
                    ratio=row["ratio"],
                    priority=row["priority"],
                    created_at=row.get("created_at"),
                    updated_at=row.get("updated_at"),
                )
                for row in rows
            ]
        finally:
            if dispose:
                await engine.dispose()

    async def upsert_fallback(self, data: dict[str, Any]) -> FallbackRule:
        rid = str(data.get("id") or uuid.uuid4())
        primary = str(data.get("primary_model") or "").strip()
        fallback = str(data.get("fallback_model") or "").strip()
        if not primary or not fallback:
            raise ValueError("primary_and_fallback_required")
        mode = str(data.get("mode") or "on_error")
        ratio_val = data.get("ratio")
        ratio: int | None = int(ratio_val) if ratio_val is not None else None
        priority_val = data.get("priority")
        priority: int | None = int(priority_val) if priority_val is not None else None
        sql = text(
            """
            INSERT INTO ai_fallbacks (id, primary_model, fallback_model, mode, ratio, priority)
            VALUES (cast(:id as uuid), :primary_model, :fallback_model, :mode, :ratio, :priority)
            ON CONFLICT (id) DO UPDATE SET
              primary_model = EXCLUDED.primary_model,
              fallback_model = EXCLUDED.fallback_model,
              mode = EXCLUDED.mode,
              ratio = EXCLUDED.ratio,
              priority = EXCLUDED.priority,
              updated_at = now()
            RETURNING id::text AS id, primary_model, fallback_model, mode, ratio, priority, created_at, updated_at
            """
        )
        params = {
            "id": rid,
            "primary_model": primary,
            "fallback_model": fallback,
            "mode": mode,
            "ratio": ratio,
            "priority": priority,
        }
        engine, dispose = await self._engine_for_call()
        try:
            async with engine.begin() as conn:
                row = (await conn.execute(sql, params)).mappings().first()
            assert row is not None
            return FallbackRule(
                id=str(row["id"]),
                primary_model=row["primary_model"],
                fallback_model=row["fallback_model"],
                mode=row["mode"],
                ratio=row["ratio"],
                priority=row["priority"],
                created_at=row.get("created_at"),
                updated_at=row.get("updated_at"),
            )
        finally:
            if dispose:
                await engine.dispose()

    async def delete_fallback(self, rule_id: str) -> None:
        sql = text("DELETE FROM ai_fallbacks WHERE id = cast(:id as uuid)")
        engine, dispose = await self._engine_for_call()
        try:
            async with engine.begin() as conn:
                await conn.execute(sql, {"id": rule_id})
        finally:
            if dispose:
                await engine.dispose()

    async def _engine_for_call(self) -> tuple[AsyncEngine, bool]:
        if self._engine is not None:
            return self._engine, False
        if self._dsn is None:
            raise RuntimeError("LLM SQL backend requires configuration")
        return get_async_engine("ai-registry", url=self._dsn), True


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
