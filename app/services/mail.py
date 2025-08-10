from __future__ import annotations

import logging
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


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
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render(self, template_name: str, context: dict[str, Any]) -> tuple[str, str]:
        html_tpl = self.env.get_template(f"{template_name}.html")
        txt_tpl = self.env.get_template(f"{template_name}.txt")
        return html_tpl.render(**context), txt_tpl.render(**context)

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
