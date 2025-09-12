from __future__ import annotations

from app.domains.auth.application.ports.mail_port import IMailer
from app.kernel.config import settings

try:  # pragma: no cover - optional dependency
    from app.domains.notifications.infrastructure.mail import (
        mail_service,  # type: ignore
    )
except Exception:  # pragma: no cover
    mail_service = None  # type: ignore


class LegacyMailAdapter(IMailer):
    async def send_verification(self, email: str, token: str) -> None:
        if mail_service is None:  # fail-open
            return
        base = getattr(settings, "public_base_url", None) or "https://example.com"
        verify_url = f"{base.rstrip('/')}/auth/verify?token={token}"
        try:
            await mail_service.send_email(
                to=email,
                subject="Verify your email",
                template="auth/verify_email",
                context={"verify_url": verify_url, "username": None},
            )
        except Exception:  # pragma: no cover - best effort
            pass

    async def send_reset_password(self, email: str, token: str) -> None:
        if mail_service is None:  # fail-open
            return
        base = getattr(settings, "public_base_url", None) or "https://example.com"
        reset_url = f"{base.rstrip('/')}/auth/reset-password?token={token}"
        try:
            await mail_service.send_email(
                to=email,
                subject="Reset your password",
                template="auth/reset_password",
                context={"reset_url": reset_url, "username": None},
            )
        except Exception:  # pragma: no cover - best effort
            pass
