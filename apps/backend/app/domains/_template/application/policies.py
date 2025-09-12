from __future__ import annotations

"""Доменные политики и правила доступа."""

from typing import Any


def can_read(subject: dict[str, Any], resource: dict[str, Any]) -> bool:
    return True


def can_write(subject: dict[str, Any], resource: dict[str, Any]) -> bool:
    return subject.get("role") in {"moderator", "admin"}

__all__ = ["can_read", "can_write"]

