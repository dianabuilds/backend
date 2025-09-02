from __future__ import annotations

import re

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


def _harden_set_cookie_line(line: str, is_https: bool) -> str:
    """
    Усиливает строку Set-Cookie безопасными флагами.
    Применяем только к интересующим нас кукам: access_token, refresh_token, session.
    """
    lower = line.lower()
    name = line.split("=", 1)[0].strip()
    target = {"access_token", "refresh_token", "session"}
    if name not in target:
        return line

    default_samesite = settings.cookie.samesite.capitalize() or "Lax"
    desired = f"samesite={default_samesite.lower()}"
    if "samesite=" in lower and desired not in lower:
        line = re.sub(r"(?i)samesite=[^;]*", f"SameSite={default_samesite}", line)
        lower = line.lower()

    parts = [line.rstrip("; ")]
    # HttpOnly
    if "httponly" not in lower:
        parts.append("HttpOnly")
    # Secure
    if "secure" not in lower and (settings.is_production or is_https):
        parts.append("Secure")
    # SameSite
    if "samesite=" not in lower:
        parts.append(f"SameSite={default_samesite}")
    # Path
    if (
        " path=" not in lower
        and not lower.strip().endswith("; path=/")
        and "path=/" not in lower
    ):
        parts.append("Path=/")
    return "; ".join(parts)


class CookiesSecurityMiddleware(BaseHTTPMiddleware):
    """
    Перехватывает все Set-Cookie и принудительно добавляет безопасные флаги
    к cookies с именами access_token, refresh_token, session.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Перестраиваем только заголовки Set-Cookie
        new_raw: list[tuple[bytes, bytes]] = []
        for k, v in response.raw_headers:
            if k.lower() == b"set-cookie":
                try:
                    s = v.decode("latin-1")
                except Exception:
                    new_raw.append((k, v))
                    continue
                hardened = _harden_set_cookie_line(s, request.url.scheme == "https")
                new_raw.append((k, hardened.encode("latin-1")))
            else:
                new_raw.append((k, v))
        response.raw_headers = new_raw

        return response
