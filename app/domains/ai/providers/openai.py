from __future__ import annotations

import os
import asyncio
from typing import Optional, Dict, Any

import httpx

from app.domains.ai.providers.base import LLMProvider, LLMResult, LLMUsage, LLMRateLimit, LLMServerError  # type: ignore


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or ""
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com").rstrip("/")

    async def complete(
        self,
        *,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: float = 30.0,
        json_mode: bool = False,
    ) -> LLMResult:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "nodes": system})
        messages.append({"role": "user", "nodes": prompt})
        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        max_attempts = int(os.getenv("AI_RETRY_ATTEMPTS", "3"))
        base_backoff = float(os.getenv("AI_RETRY_BACKOFF", "1.0"))
        req_timeout = float(os.getenv("AI_REQUEST_TIMEOUT", str(timeout or 30.0)))

        last_exc: Exception | None = None
        async with httpx.AsyncClient(timeout=req_timeout) as client:
            for attempt in range(1, max_attempts + 1):
                try:
                    resp = await client.post(url, headers=headers, json=body)
                    if resp.status_code == 429:
                        raise LLMRateLimit(resp.text)
                    if resp.status_code >= 500:
                        raise LLMServerError(resp.text)
                    resp.raise_for_status()
                    data = resp.json()
                    choice = (data.get("choices") or [{}])[0]
                    msg = choice.get("message", {}) or {}
                    content = msg.get("nodes", "") or ""
                    usage = data.get("usage", {}) or {}
                    return LLMResult(
                        text=content,
                        model=data.get("model", model),
                        usage=LLMUsage(
                            prompt_tokens=int(usage.get("prompt_tokens", 0)),
                            completion_tokens=int(usage.get("completion_tokens", 0)),
                        ),
                        raw=data,
                    )
                except (LLMRateLimit, LLMServerError, httpx.HTTPError) as e:
                    last_exc = e
                    if attempt >= max_attempts:
                        raise
                    try:
                        import random
                        sleep_for = base_backoff * (2 ** (attempt - 1)) * (0.8 + 0.4 * random.random())
                    except Exception:
                        sleep_for = base_backoff * (2 ** (attempt - 1))
                    await asyncio.sleep(sleep_for)

        if last_exc:
            raise last_exc
        raise RuntimeError("OpenAIProvider: unexpected state")
