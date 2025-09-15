from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Any

from apps.backendDDD.domains.platform.notifications.logic.dispatcher import (
    register_channel,
)
from apps.backendDDD.packages.core.config import Settings


def register_email_channel(settings: Settings, name: str = "email") -> None:
    """Register SMTP-backed email notification channel.

    Payload contract (minimal):
    {"to": ["user@example.com"], "subject": "...", "text": "...", "html": "..."}
    Unknown fields are ignored. On mock mode or missing SMTP host, logs instead of sending.
    """

    log = logging.getLogger("notifications.email")

    def _send(payload: dict[str, Any]) -> None:
        to = payload.get("to")
        subject = str(payload.get("subject", ""))
        text = payload.get("text")
        html = payload.get("html")
        if not to:
            log.warning("email channel missing 'to'")
            return
        recipients = to if isinstance(to, list) else [str(to)]

        if settings.smtp_mock or not settings.smtp_host:
            log.info("[MOCK] email -> %s | %s", recipients, subject)
            return

        msg = EmailMessage()
        msg["Subject"] = subject
        frm = settings.smtp_mail_from or "noreply@example.com"
        if settings.smtp_mail_from_name:
            msg["From"] = f"{settings.smtp_mail_from_name} <{frm}>"
        else:
            msg["From"] = frm
        msg["To"] = ", ".join(recipients)
        if html:
            msg.add_alternative(str(html), subtype="html")
            if text:
                msg.set_content(str(text))
        else:
            msg.set_content(str(text or ""))

        try:
            with smtplib.SMTP(
                settings.smtp_host, int(settings.smtp_port or 25), timeout=10
            ) as s:
                if settings.smtp_tls:
                    s.starttls()
                if settings.smtp_username and settings.smtp_password:
                    s.login(settings.smtp_username, settings.smtp_password)
                s.send_message(msg)
        except Exception:
            log.exception("SMTP send failed")

    register_channel(name, _send)


__all__ = ["register_email_channel"]
