from __future__ import annotations

import time
from typing import Annotated, Any
from urllib.parse import urljoin

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.repositories.system_v2_repository import (
    ModelsRepository,
    ProvidersRepository,
)
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/ai/system",
    tags=["admin-ai-system"],
    responses=ADMIN_AUTH_RESPONSES,
)

AdminRequired = Annotated[None, Depends(require_admin_role())]


@router.get("/models")
async def list_models(
    _: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> list[dict[str, Any]]:
    repo = ModelsRepository(db)
    rows = await repo.list()
    return [
        {
            "id": str(r.id),
            "provider_id": str(r.provider_id),
            "code": r.code,
            "name": r.name,
            "family": r.family,
            "capabilities": r.capabilities,
            "inputs": r.inputs,
            "limits": r.limits,
            "pricing": r.pricing,
            "enabled": bool(r.enabled),
        }
        for r in rows
    ]


@router.post("/models")
async def create_model(
    payload: dict[str, Any] = Body(...),
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = ModelsRepository(db)
    row = await repo.create(payload)
    return {
        "id": str(row.id),
        "provider_id": str(row.provider_id),
        "code": row.code,
        "name": row.name,
        "family": row.family,
        "capabilities": row.capabilities,
        "inputs": row.inputs,
        "limits": row.limits,
        "pricing": row.pricing,
        "enabled": bool(row.enabled),
    }


@router.put("/models/{model_id}")
async def update_model(
    model_id: str,
    payload: dict[str, Any] = Body(...),
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = ModelsRepository(db)
    row = await repo.update(model_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="model not found")
    return {
        "id": str(row.id),
        "provider_id": str(row.provider_id),
        "code": row.code,
        "name": row.name,
        "family": row.family,
        "capabilities": row.capabilities,
        "inputs": row.inputs,
        "limits": row.limits,
        "pricing": row.pricing,
        "enabled": bool(row.enabled),
    }


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = ModelsRepository(db)
    await repo.delete(model_id)
    return {"ok": True}


@router.post("/models/{model_id}/test")
async def test_model(
    model_id: str,
    payload: dict[str, Any] = Body(default={}),
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    mrepo = ModelsRepository(db)
    prep = ProvidersRepository(db)
    row = await mrepo.get(model_id)
    if row is None:
        raise HTTPException(status_code=404, detail="model not found")
    provider = await prep.get(str(row.provider_id))
    if provider is None:
        raise HTTPException(status_code=404, detail="provider not found")

    mf = provider.manifest or {}
    caps = set(row.capabilities or [])
    task = payload.get("task") or ("chat" if "chat" in caps else "embed")
    ep = (mf.get("endpoints") or {}).get(task) or {}
    base = (provider.base_url or "").rstrip("/")
    path = ep.get("path") or ("/v1/chat/completions" if task == "chat" else "/v1/embeddings")
    method = (ep.get("method") or "POST").upper()
    # Robustly join base and path; avoid duplicate segments
    if path.startswith("http"):
        url = path
    else:
        # If base already contains API version or endpoint, treat it as full endpoint.
        from urllib.parse import urlparse

        parsed = urlparse(base)
        if (
            parsed.scheme
            and parsed.netloc
            and parsed.path
            and any(seg in parsed.path for seg in ("/v1/", "/chat/completions", "/embeddings"))
        ):
            url = base
        else:
            # Ensure trailing slash for correct urljoin behavior
            base_for_join = (base + "/") if base else ""
            url = urljoin(base_for_join, path.lstrip("/"))

    headers: dict[str, str] = {"Content-Type": "application/json"}
    typ = ((mf.get("auth") or {}).get("type") or "bearer").lower()
    token = None
    try:
        secrets = await prep.list_secrets(str(provider.id))
        # Prefer common keys if present
        preferred = {"api_key", "token", "secret", "authorization", "auth"}
        token = None
        for s in secrets or []:
            try:
                k = (getattr(s, "key", "") or "").lower()
                if k in preferred and getattr(s, "value_encrypted", None):
                    token = s.value_encrypted
                    break
            except Exception:
                pass
        if token is None and secrets:
            token = secrets[0].value_encrypted
    except Exception:
        token = None
    # Fallback: some setups store API key in provider.code
    if not token and getattr(provider, "code", None):
        token = str(provider.code)
    used_auth = "none"
    if token and typ in {"bearer", "api_key"}:
        headers["Authorization"] = f"Bearer {token}"
        used_auth = "bearer"

    prompt = payload.get("prompt") or "ping"
    if task == "chat":
        body = {
            "model": row.code,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1,
        }
    else:
        body = {"model": row.code, "input": prompt}

    try:
        timeout = httpx.Timeout(timeout=30.0, connect=10.0, read=25.0, write=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            t0 = time.perf_counter()
            resp = await client.request(method, url, headers=headers, json=body)
            latency = (time.perf_counter() - t0) * 1000
    except (
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        httpx.WriteTimeout,
        httpx.TimeoutException,
    ) as e:
        # Return structured timeout without raising HTTP error to the admin UI
        has_auth_hdr = "Authorization" in headers
        debug_prefix = (
            f"timeout; auth={used_auth}; has_auth={has_auth_hdr}; url={url}; method={method} -> "
        )
        return {
            "ok": False,
            "status": 0,
            "latency_ms": None,
            "url": url,
            "method": method,
            "auth": used_auth,
            "excerpt": (debug_prefix + str(e))[:400],
        }
    except Exception as e:
        has_auth_hdr = "Authorization" in headers
        debug_prefix = (
            f"error; auth={used_auth}; has_auth={has_auth_hdr}; url={url}; method={method} -> "
        )
        return {
            "ok": False,
            "status": 0,
            "latency_ms": None,
            "url": url,
            "method": method,
            "auth": used_auth,
            "excerpt": (debug_prefix + str(e))[:400],
        }

    ok = 200 <= resp.status_code < 300
    try:
        data = resp.json()
        remote_excerpt = str(data)[:400]
    except Exception:
        remote_excerpt = resp.text[:400]

    # Do not leak secrets; only boolean flags
    has_auth_hdr = "Authorization" in headers
    debug_prefix = f"auth={used_auth}; has_auth={has_auth_hdr}; url={url}; method={method} -> "
    excerpt = (debug_prefix + remote_excerpt)[:400]
    return {
        "ok": ok,
        "status": resp.status_code,
        "latency_ms": round(latency, 2),
        "url": url,
        "method": method,
        "auth": used_auth,
        "excerpt": excerpt,
    }
