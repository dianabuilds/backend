from __future__ import annotations

import os
import asyncio
import time
from typing import Optional, Dict, Any

import httpx

from app.domains.ai.providers.base import (
    LLMProvider,
    LLMResult,
    LLMUsage,
    LLMRateLimit,
    LLMServerError,
)


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or ""
        self.base_url = (base_url or os.getenv("ANTHROPIC_BASE_URL") or "https://api.anthropic.com").rstrip("/")

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
        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "nodes": prompt}],
        }

        max_attempts = int(os.getenv("AI_RETRY_ATTEMPTS", "3"))
        base_backoff = float(os.getenv("AI_RETRY_BACKOFF", "1.0"))
        req_timeout = float(os.getenv("AI_REQUEST_TIMEOUT", str(timeout or 30.0)))

        last_exc: Exception | None = None
        async with httpx.AsyncClient(timeout=req_timeout) as client:
            for attempt in range(1, max_attempts + 1):
                try:
                    t0 = time.perf_counter()
                    resp = await client.post(url, headers=headers, json=body)
                    dt = time.perf_counter() - t0
                    if resp.status_code == 429:
                        raise LLMRateLimit(resp.text)
                    if resp.status_code >= 500:
                        raise LLMServerError(resp.text)
                    resp.raise_for_status()
                    data = resp.json()
                    content = ""
                    try:
                        blocks = data.get("nodes", [])
                        if blocks and isinstance(blocks, list):
                            content = "".join([blk.get("text", "") for blk in blocks if isinstance(blk, dict)])
                    except Exception:
                        content = ""
                    usage_raw = data.get("usage", {}) or {}
                    return LLMResult(
                        text=content or "",
                        model=data.get("model", model),
                        usage=LLMUsage(
                            prompt_tokens=int(usage_raw.get("input_tokens", 0)),
                            completion_tokens=int(usage_raw.get("output_tokens", 0)),
                            latency=dt,
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
        raise RuntimeError("AnthropicProvider: unexpected state")

    async def count_tokens(
        self,
        *,
        model: str,
        prompt: str,
        system: Optional[str] = None,
    ) -> Optional[int]:
        url = f"{self.base_url}/v1/messages/tokens"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body: Dict[str, Any] = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        if system:
            body["messages"].insert(0, {"role": "system", "content": system})
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                tok = data.get("input_tokens") or data.get("tokens")
                return int(tok) if tok is not None else None
        except Exception:
            return None
