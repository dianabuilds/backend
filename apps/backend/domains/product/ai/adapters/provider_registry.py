from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

import httpx

from domains.product.ai.application.ports import Provider
from domains.product.ai.application.registry import LLMModelCfg, LLMProviderCfg, LLMRegistry


class RegistryBackedProvider(Provider):
    def __init__(
        self,
        registry: LLMRegistry,
        *,
        fallback: Provider | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.registry = registry
        self.fallback = fallback
        self.timeout = timeout

    async def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        provider: str | None = None,
        model_id: str | None = None,
    ) -> str:
        try:
            model_cfg = await self._resolve_model(model_id=model_id, name=model)
            provider_cfg = await self._resolve_provider(
                provider or (model_cfg.provider_slug if model_cfg else None)
            )
            if not provider_cfg or provider_cfg.enabled is False or not provider_cfg.base_url:
                raise RuntimeError("provider_not_configured")
            text = await self._call_provider(provider_cfg, model_cfg, prompt)
            if not text:
                raise RuntimeError("empty_response")
            return text
        except Exception as exc:
            if (
                isinstance(exc, RuntimeError)
                and str(exc) == "provider_not_configured"
                and self.fallback is not None
            ):
                return await self.fallback.generate(
                    prompt,
                    model=model,
                    provider=provider,
                    model_id=model_id,
                )
            raise

    async def _resolve_model(self, *, model_id: str | None, name: str | None) -> LLMModelCfg | None:
        models = await self.registry.list_models()
        for item in models:
            if model_id and item.id == model_id:
                return item
        if name:
            for item in models:
                if item.name == name:
                    return item
        return None

    async def _resolve_provider(self, slug: str | None) -> LLMProviderCfg | None:
        if not slug:
            return None
        providers = await self.registry.list_providers()
        for item in providers:
            if item.slug == slug:
                return item
        return None

    async def _call_provider(
        self,
        provider: LLMProviderCfg,
        model_cfg: LLMModelCfg | None,
        prompt: str,
    ) -> str | None:
        extras = provider.extras or {}
        base_url = provider.base_url or ""
        prompt_mode = str(
            extras.get("prompt_mode")
            or ("openai_chat" if "chat/completions" in base_url else "text")
        )
        prompt_key = str(
            extras.get("prompt_key")
            or ("messages" if prompt_mode in {"openai_chat", "openai-chat"} else "prompt")
        )
        response_path = extras.get("response_path")
        if not response_path and prompt_mode in {"openai_chat", "openai-chat"}:
            response_path = "choices.0.message.content"
        include_model = extras.get("include_model")
        if include_model is None:
            include_model = True
        include_version = extras.get("include_version")
        if include_version is None:
            include_version = bool(model_cfg and model_cfg.version)
        method = str(extras.get("method") or "POST").upper()
        url = str(extras.get("endpoint") or provider.base_url or "")
        if not url:
            raise RuntimeError("provider_not_configured")

        payload: dict[str, Any] = {}
        if prompt_mode in {"openai_chat", "openai-chat"}:
            role = str(extras.get("prompt_role") or "user")
            payload[prompt_key] = [{"role": role, "content": prompt}]
        elif prompt_mode in {"json", "json_raw"}:
            try:
                payload[prompt_key] = json.loads(prompt)
            except json.JSONDecodeError as err:
                raise ValueError("prompt_json_invalid") from err
        else:
            payload[prompt_key] = prompt

        model_name = model_cfg.name if model_cfg else extras.get("model_fallback")
        if include_model and model_name:
            model_key = str(extras.get("model_key") or "model")
            if model_key:
                payload[model_key] = model_name

        version_value = model_cfg.version if model_cfg and model_cfg.version else None
        if include_version and version_value:
            version_key = str(extras.get("version_key") or "version")
            if version_key:
                payload[version_key] = version_value

        overrides = extras.get("payload_overrides")
        if isinstance(overrides, dict):
            payload.update(overrides)

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if provider.api_key:
            header_name = str(extras.get("auth_header") or "Authorization")
            prefix = str(extras.get("auth_prefix") or "Bearer ")
            headers[header_name] = f"{prefix}{provider.api_key}"
        headers_override = extras.get("headers")
        if isinstance(headers_override, dict):
            headers.update({str(k): str(v) for k, v in headers_override.items()})

        params = (
            extras.get("query_params") if isinstance(extras.get("query_params"), dict) else None
        )

        timeout_value = extras.get("timeout_sec") or provider.timeout_sec or self.timeout
        timeout = httpx.Timeout(timeout_value, connect=min(5.0, timeout_value))

        async with httpx.AsyncClient(timeout=timeout) as client:
            if method == "GET":
                response = await client.get(
                    url, params={**(params or {}), **payload}, headers=headers
                )
            else:
                response = await client.post(url, params=params, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        text = self._extract_text(data, response_path)
        if isinstance(text, (list, tuple)):
            text = "\n".join(str(item) for item in text)
        return str(text) if text is not None else None

    def _extract_text(self, data: Any, response_path: Any) -> Any:
        if response_path:
            parts = [p for p in str(response_path).split(".") if p]
            value: Any = data
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                elif isinstance(value, list):
                    try:
                        index = int(part)
                        value = value[index]
                    except (ValueError, IndexError):
                        return None
                else:
                    return None
            return value
        if isinstance(data, dict):
            if data.get("result"):
                return data["result"]
            if data.get("text"):
                return data["text"]
            if isinstance(data.get("choices"), Iterable):
                choices = list(data["choices"] if isinstance(data["choices"], Iterable) else [])
                if choices:
                    first = choices[0]
                    if isinstance(first, dict):
                        return first.get("text") or first.get("message", {}).get("content")
                    return first
        return data


__all__ = ["RegistryBackedProvider"]
