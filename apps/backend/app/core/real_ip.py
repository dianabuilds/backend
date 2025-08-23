from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Optional

from fastapi import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings


def _is_trusted(remote: str) -> bool:
    try:
        rip = ip_address(remote)
    except ValueError:
        return False
    for proxy in settings.real_ip.trusted_proxies:
        try:
            if rip in ip_network(proxy):
                return True
        except ValueError:
            continue
    return False


def get_real_ip(request: Request) -> Optional[str]:
    """Return best-effort real client IP address."""
    if not settings.real_ip.enabled or not request.client:
        return request.client.host if request.client else None
    remote = request.client.host
    if not _is_trusted(remote):
        return remote

    header = settings.real_ip.header
    depth = settings.real_ip.depth

    if header == "X-Forwarded-For":
        value = request.headers.get("X-Forwarded-For")
        if value:
            parts = [p.strip() for p in value.split(",") if p.strip()]
            if not parts:
                return remote
            if depth is None:
                return parts[0]
            if len(parts) >= depth:
                return parts[-depth]
    elif header == "Forwarded":
        value = request.headers.get("Forwarded")
        if value:
            forwards = [p.strip() for p in value.split(",") if p.strip()]
            if not forwards:
                return remote
            if depth is None:
                section = forwards[0]
            elif len(forwards) >= depth:
                section = forwards[-depth]
            else:
                return remote
            for token in section.split(";"):
                token = token.strip()
                if token.startswith("for="):
                    candidate = token[4:].strip('"')
                    if candidate.startswith("["):
                        candidate = candidate.split("]")[0][1:]
                    else:
                        candidate = candidate.split(":")[0]
                    return candidate
    elif header == "CF-Connecting-IP":
        value = request.headers.get("CF-Connecting-IP")
        if value:
            return value.strip()
    return remote


class RealIPMiddleware:
    """ASGI middleware to rewrite client IP based on proxy headers."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in {"http", "websocket"} and scope.get("client"):
            request = Request(scope)
            real = get_real_ip(request)
            if real:
                scope["client"] = (real, scope["client"][1])
        await self.app(scope, receive, send)
