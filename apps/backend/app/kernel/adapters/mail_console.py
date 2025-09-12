from __future__ import annotations

import asyncio
import json
from typing import Iterable, Mapping, Optional

from app.kernel.mail import AbstractMailService


class ConsoleMailService(AbstractMailService):
    def __init__(self, default_sender: Optional[str] = None) -> None:
        self._default_sender = default_sender

    async def send(
        self,
        to: Iterable[str],
        subject: str,
        text_body: Optional[str] = None,
        html_body: Optional[str] = None,
        *,
        sender: Optional[str] = None,
        cc: Optional[Iterable[str]] = None,
        bcc: Optional[Iterable[str]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        s = sender or self._default_sender or "noreply@example.local"
        payload = {
            "type": "console_email",
            "from": s,
            "to": list(to),
            "subject": subject,
            "text": text_body,
            "html": html_body,
            "cc": list(cc) if cc else None,
            "bcc": list(bcc) if bcc else None,
            "headers": dict(headers) if headers else None,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        await asyncio.sleep(0)

    async def close(self) -> None:
        await asyncio.sleep(0)


class NullMailService(AbstractMailService):
    async def send(
        self,
        to: Iterable[str],
        subject: str,
        text_body: Optional[str] = None,
        html_body: Optional[str] = None,
        *,
        sender: Optional[str] = None,
        cc: Optional[Iterable[str]] = None,
        bcc: Optional[Iterable[str]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        return None

    async def close(self) -> None:
        return None


__all__ = ["ConsoleMailService", "NullMailService"]

