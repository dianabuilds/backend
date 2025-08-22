from __future__ import annotations

from app.domains.auth.application.ports.mail_port import IMailer

try:
    from app.services.mail import mail_service  # type: ignore
except Exception:  # pragma: no cover
    mail_service = None  # type: ignore


class LegacyMailAdapter(IMailer):
    async def send_verification(self, email: str, token: str) -> None:
        if mail_service is None:  # fail-open
            return
        await mail_service.send_verification(email, token)  # type: ignore
