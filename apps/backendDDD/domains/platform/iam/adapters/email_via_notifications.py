from __future__ import annotations

from typing import Any

from apps.backendDDD.domains.platform.iam.ports.email_port import EmailSender
from apps.backendDDD.domains.platform.notifications.logic.dispatcher import dispatch


class EmailViaNotifications(EmailSender):
    async def send(
        self,
        to: list[str],
        subject: str,
        text: str | None = None,
        html: str | None = None,
    ) -> None:
        payload: dict[str, Any] = {"to": to, "subject": subject}
        if text:
            payload["text"] = text
        if html:
            payload["html"] = html
        # Dispatch synchronously (wrapping async into sync sender)
        dispatch("email", payload)


__all__ = ["EmailViaNotifications"]
