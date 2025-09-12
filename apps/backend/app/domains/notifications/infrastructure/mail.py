from __future__ import annotations

import logging
from email.message import EmailMessage
from typing import Any

import aiosmtplib

from app.kernel.config import settings
from app.kernel.templates import render as render_template

logger = logging.getLogger(__name__)


class MailService:
    def __init__(self) -> None:
        self.host = settings.smtp.host
        self.port = settings.smtp.port
        self.username = settings.smtp.username
        self.password = settings.smtp.password
        self.use_tls = settings.smtp.tls
        self.mail_from = settings.smtp.mail_from
        self.from_name = settings.smtp.mail_from_name
        self.mock = settings.smtp.mock

    @staticmethod
    def _split_template(template: str) -> tuple[str | None, str]:
        """Split "domain/name" into (domain, name)."""
        if "/" in template:
            d, n = template.split("/", 1)
            return d or None, n
        return None, template

    def render(self, template: str, context: dict[str, Any]) -> tuple[str, str]:
        domain, name = self._split_template(template)
        html = render_template(domain, f"{name}.html", context)
        text = render_template(domain, f"{name}.txt", context)
        return html, text

    async def send_email(
        self,
        to: str,
        subject: str,
        template: str,
        context: dict[str, Any],
    ) -> None:
        html, text = self.render(template, context)
        msg = EmailMessage()
        msg["From"] = f"{self.from_name} <{self.mail_from}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(text)
        msg.add_alternative(html, subtype="html")

        if self.mock:
            logger.info("Mock email to %s: %s", to, subject)
            return
        try:
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                start_tls=self.use_tls,
                timeout=10,
            )
            logger.info("Email sent to %s: %s", to, subject)
        except Exception as exc:
            logger.warning("Failed to send email to %s: %s", to, exc)
            raise


mail_service = MailService()
