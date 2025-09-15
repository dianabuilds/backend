from __future__ import annotations


def validate_username(username: str) -> None:
    if not username or len(username) < 3:
        raise ValueError("username too short")
