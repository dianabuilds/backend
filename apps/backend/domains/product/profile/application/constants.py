from __future__ import annotations

from collections.abc import Mapping
from typing import Any

NOT_FOUND_CODES = frozenset({"profile_not_found", "email_change_not_found"})


def normalize_subject(subject: Mapping[str, Any]) -> dict[str, Any]:
    """Return a shallow copy suitable for passing to services."""

    return dict(subject)


__all__ = [
    "NOT_FOUND_CODES",
    "normalize_subject",
]
