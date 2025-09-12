from __future__ import annotations

from .mail_adapter import LegacyMailAdapter


def get_mailer() -> LegacyMailAdapter:
    return LegacyMailAdapter()


__all__ = ["get_mailer", "LegacyMailAdapter"]

