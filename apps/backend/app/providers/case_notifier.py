from __future__ import annotations

from typing import Protocol
from uuid import UUID

import httpx

from app.kernel.config import Settings, get_settings
from app.providers.email import IEmail


class ICaseNotifier(Protocol):
    async def case_created(self, case_id: UUID) -> None: ...


class FakeCaseNotifier(ICaseNotifier):
    async def case_created(self, case_id: UUID) -> None:  # pragma: no cover
        return None


class SandboxCaseNotifier(FakeCaseNotifier):
    pass


class RealCaseNotifier(ICaseNotifier):
    def __init__(self, email: IEmail, settings: Settings | None = None) -> None:
        self._email = email
        self._settings = settings or get_settings()

    async def case_created(self, case_id: UUID) -> None:
        settings = self._settings.moderation
        subject = f"Moderation case {case_id} created"
        body = subject
        for recipient in settings.notify_emails:
            try:
                await self._email.send(recipient, subject, body)
            except Exception:  # pragma: no cover - best effort
                pass
        if settings.slack_webhook_url:
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(settings.slack_webhook_url, json={"text": body})
                except Exception:  # pragma: no cover - best effort
                    pass
