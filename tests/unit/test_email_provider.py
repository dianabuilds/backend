import aiosmtplib
import pytest
from apps.backend.app.core.app_settings.smtp import SMTPSettings
from apps.backend.app.core.settings import Settings
from apps.backend.app.providers.email import RealEmail


@pytest.mark.asyncio
async def test_real_email_send_skips_when_mock(monkeypatch):
    called = False

    async def fake_send(*args, **kwargs):  # pragma: no cover
        nonlocal called
        called = True

    monkeypatch.setattr(aiosmtplib, "send", fake_send)

    settings = Settings(smtp=SMTPSettings(mock=True))
    email = RealEmail(settings=settings)
    await email.send("to@example.com", "Subject", "body")

    assert called is False


@pytest.mark.asyncio
async def test_real_email_send_calls_aiosmtplib(monkeypatch):
    captured = {}

    async def fake_send(message, **kwargs):
        captured["message"] = message
        captured.update(kwargs)

    monkeypatch.setattr(aiosmtplib, "send", fake_send)

    smtp_settings = SMTPSettings(
        mock=False,
        host="smtp.example.com",
        port=587,
        username="user",
        password="pass",
        tls=True,
    )
    settings = Settings(smtp=smtp_settings)
    email = RealEmail(settings=settings)
    await email.send("to@example.com", "Subject", "Body")

    assert captured["message"]["To"] == "to@example.com"
    assert captured["hostname"] == "smtp.example.com"
    assert captured["port"] == 587
    assert captured["username"] == "user"
    assert captured["password"] == "pass"
    assert captured["start_tls"] is True
