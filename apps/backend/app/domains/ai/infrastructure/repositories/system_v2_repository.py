from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.models.ai_system_v2 import (
    AIDefaults,
    AIEvalRun,
    AIModel,
    AIPreset,
    AIProvider,
    AIProviderSecret,
    AIRoutingProfile,
)


class ProvidersRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self) -> list[AIProvider]:
        res = await self._db.execute(select(AIProvider).order_by(AIProvider.code))
        return list(res.scalars())

    async def get(self, provider_id: str) -> AIProvider | None:
        res = await self._db.execute(select(AIProvider).where(AIProvider.id == provider_id))
        return res.scalar_one_or_none()

    async def create(self, data: dict[str, Any]) -> AIProvider:
        row = AIProvider(
            code=data.get("code"),
            name=data.get("name"),
            base_url=data.get("base_url"),
            manifest=data.get("manifest"),
            health=data.get("health"),
        )
        self._db.add(row)
        await self._db.flush()
        return row

    async def update(self, provider_id: str, patch: dict[str, Any]) -> AIProvider | None:
        row = await self.get(provider_id)
        if row is None:
            return None
        for k in ("code", "name", "base_url", "health"):
            if k in patch:
                setattr(row, k, patch[k])
        if "manifest" in patch:
            row.manifest = patch["manifest"]
        await self._db.flush()
        return row

    async def delete(self, provider_id: str) -> None:
        await self._db.execute(delete(AIProvider).where(AIProvider.id == provider_id))

    async def set_secrets(self, provider_id: str, secrets: dict[str, str]) -> None:
        # overwrite keys provided; remove keys with empty values
        for key, value in secrets.items():
            if value is None:
                continue
            res = await self._db.execute(
                select(AIProviderSecret).where(
                    AIProviderSecret.provider_id == provider_id,
                    AIProviderSecret.key == key,
                )
            )
            row = res.scalar_one_or_none()
            if value == "":
                if row is not None:
                    await self._db.delete(row)
                continue
            if row is None:
                row = AIProviderSecret(provider_id=provider_id, key=key, value_encrypted=value)
                self._db.add(row)
            else:
                row.value_encrypted = value
        await self._db.flush()

    async def list_secrets(self, provider_id: str) -> list[AIProviderSecret]:
        res = await self._db.execute(
            select(AIProviderSecret).where(AIProviderSecret.provider_id == provider_id)
        )
        return list(res.scalars())


class ModelsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self) -> list[AIModel]:
        res = await self._db.execute(select(AIModel))
        return list(res.scalars())

    async def get(self, model_id: str) -> AIModel | None:
        res = await self._db.execute(select(AIModel).where(AIModel.id == model_id))
        return res.scalar_one_or_none()

    async def get_with_provider(self, model_id: str) -> tuple[AIModel | None, AIProvider | None]:
        res = await self._db.execute(select(AIModel).where(AIModel.id == model_id))
        m = res.scalar_one_or_none()
        if m is None:
            return None, None
        pres = await self._db.execute(select(AIProvider).where(AIProvider.id == m.provider_id))
        p = pres.scalar_one_or_none()
        return m, p

    async def upsert_from_manifest(self, provider_id: str, model: dict[str, Any]) -> AIModel:
        code = model.get("id")
        res = await self._db.execute(
            select(AIModel).where(AIModel.provider_id == provider_id, AIModel.code == code)
        )
        row = res.scalar_one_or_none()
        if row is None:
            row = AIModel(provider_id=provider_id, code=code)
            self._db.add(row)
        row.name = model.get("name")
        row.family = model.get("family")
        row.capabilities = model.get("capabilities")
        row.inputs = model.get("inputs")
        row.limits = model.get("limits")
        row.pricing = model.get("pricing")
        await self._db.flush()
        return row

    async def create(self, data: dict[str, Any]) -> AIModel:
        row = AIModel(
            provider_id=data["provider_id"],
            code=data["code"],
            name=data.get("name"),
            family=data.get("family"),
            capabilities=data.get("capabilities"),
            inputs=data.get("inputs"),
            limits=data.get("limits"),
            pricing=data.get("pricing"),
            enabled=bool(data.get("enabled", True)),
        )
        self._db.add(row)
        await self._db.flush()
        return row

    async def update(self, model_id: str, patch: dict[str, Any]) -> AIModel | None:
        row = await self.get(model_id)
        if row is None:
            return None
        for k in (
            "code",
            "name",
            "family",
            "capabilities",
            "inputs",
            "limits",
            "pricing",
            "enabled",
        ):
            if k in patch:
                setattr(row, k, patch[k])
        await self._db.flush()
        return row

    async def delete(self, model_id: str) -> None:
        await self._db.execute(delete(AIModel).where(AIModel.id == model_id))


class DefaultsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self) -> AIDefaults | None:
        res = await self._db.execute(select(AIDefaults).where(AIDefaults.id == "1"))
        return res.scalar_one_or_none()

    async def set(
        self, provider_id: str | None, model_id: str | None, bundle_id: str | None
    ) -> AIDefaults:
        row = await self.get()
        if row is None:
            row = AIDefaults(id="1")
            self._db.add(row)
        row.provider_id = provider_id
        row.model_id = model_id
        row.bundle_id = bundle_id
        await self._db.flush()
        return row


class ProfilesRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self) -> list[AIRoutingProfile]:
        res = await self._db.execute(select(AIRoutingProfile).order_by(AIRoutingProfile.name))
        return list(res.scalars())

    async def get(self, profile_id: str) -> AIRoutingProfile | None:
        res = await self._db.execute(
            select(AIRoutingProfile).where(AIRoutingProfile.id == profile_id)
        )
        return res.scalar_one_or_none()

    async def create(self, data: dict[str, Any]) -> AIRoutingProfile:
        row = AIRoutingProfile(
            name=data["name"],
            enabled=bool(data.get("enabled", True)),
            rules=data.get("rules", []),
        )
        self._db.add(row)
        await self._db.flush()
        return row

    async def update(self, profile_id: str, patch: dict[str, Any]) -> AIRoutingProfile | None:
        row = await self.get(profile_id)
        if row is None:
            return None
        for k in ("name", "enabled", "rules"):
            if k in patch:
                setattr(row, k, patch[k])
        await self._db.flush()
        return row

    async def delete(self, profile_id: str) -> None:
        await self._db.execute(delete(AIRoutingProfile).where(AIRoutingProfile.id == profile_id))


class PresetsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self) -> list[AIPreset]:
        res = await self._db.execute(select(AIPreset).order_by(AIPreset.name))
        return list(res.scalars())

    async def get(self, preset_id: str) -> AIPreset | None:
        res = await self._db.execute(select(AIPreset).where(AIPreset.id == preset_id))
        return res.scalar_one_or_none()

    async def create(self, data: dict[str, Any]) -> AIPreset:
        row = AIPreset(name=data["name"], task=data["task"], params=data.get("params", {}))
        self._db.add(row)
        await self._db.flush()
        return row

    async def update(self, preset_id: str, patch: dict[str, Any]) -> AIPreset | None:
        row = await self.get(preset_id)
        if row is None:
            return None
        for k in ("name", "task", "params"):
            if k in patch:
                setattr(row, k, patch[k])
        await self._db.flush()
        return row

    async def delete(self, preset_id: str) -> None:
        await self._db.execute(delete(AIPreset).where(AIPreset.id == preset_id))


class EvalRunsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, spec: dict[str, Any], profile_id: str | None = None) -> AIEvalRun:
        row = AIEvalRun(spec=spec, profile_id=profile_id, status="queued")
        self._db.add(row)
        await self._db.flush()
        return row
