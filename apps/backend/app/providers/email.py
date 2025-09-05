from __future__ import annotations

import logging
from email.message import EmailMessage
from typing import Protocol

import aiosmtplib

from app.core.settings import Settings, get_settings


class IEmail(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


logger = logging.getLogger(__name__)


class RealEmail(IEmail):
    """SMTP-based email provider."""

    def __init__(self, settings=None) -> None:
        self._settings: Settings = settings or get_settings()

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email via SMTP.

        If ``settings.smtp.mock`` is true, the message is not actually sent but
        the call succeeds to make testing easier.
        """

        smtp = self._settings.smtp

        msg = EmailMessage()
        msg["From"] = f"{smtp.mail_from_name} <{smtp.mail_from}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        if smtp.mock:  # pragma: no cover - simple guard
            logger.info("Mock email to %s: %s", to, subject)
            return

        await aiosmtplib.send(
            msg,
            hostname=smtp.host,
            port=smtp.port,
            username=smtp.username,
            password=smtp.password,
            start_tls=smtp.tls,
            timeout=10,
        )
