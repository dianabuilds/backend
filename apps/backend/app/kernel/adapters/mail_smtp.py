from __future__ import annotations

import asyncio
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Iterable, Mapping, Optional

from app.kernel.mail import AbstractMailService


@dataclass
class SmtpConfig:
    host: str
    port: int = 25
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = False
    starttls: bool = False
    default_sender: Optional[str] = None
    timeout: Optional[float] = 10.0


class SMTPMailService(AbstractMailService):
    def __init__(self, cfg: SmtpConfig) -> None:
        self._cfg = cfg

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
        if not text_body and not html_body:
            raise ValueError("Either text_body or html_body must be provided")
        msg = EmailMessage()
        s = sender or self._cfg.default_sender
        if not s:
            raise ValueError("Sender is required (provide sender or configure default_sender)")
        msg["From"] = s
        to_list = list(to)
        if not to_list:
            raise ValueError("At least one recipient is required")
        msg["To"] = ", ".join(to_list)
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg["Subject"] = subject
        if headers:
            for k, v in headers.items():
                msg[k] = v
        if text_body and html_body:
            msg.set_content(text_body)
            msg.add_alternative(html_body, subtype="html")
        elif html_body:
            msg.add_alternative(html_body, subtype="html")
        else:
            msg.set_content(text_body or "")
        recipients = to_list[:]
        if cc:
            recipients.extend(list(cc))
        if bcc:
            recipients.extend(list(bcc))
        await asyncio.to_thread(self._send_smtp, msg, recipients)

    def _send_smtp(self, msg: EmailMessage, recipients: list[str]) -> None:
        cfg = self._cfg
        connect_kwargs = {}
        if cfg.timeout is not None:
            connect_kwargs["timeout"] = float(cfg.timeout)
        if cfg.use_tls:
            smtp = smtplib.SMTP_SSL(cfg.host, cfg.port, **connect_kwargs)
        else:
            smtp = smtplib.SMTP(cfg.host, cfg.port, **connect_kwargs)
        try:
            smtp.ehlo()
            if cfg.starttls and not cfg.use_tls:
                smtp.starttls(); smtp.ehlo()
            if cfg.username:
                smtp.login(cfg.username, cfg.password or "")
            smtp.send_message(msg, from_addr=msg["From"], to_addrs=recipients)
        finally:
            try:
                smtp.quit()
            except Exception:
                smtp.close()

    async def close(self) -> None:
        return None


__all__ = ["SmtpConfig", "SMTPMailService"]

