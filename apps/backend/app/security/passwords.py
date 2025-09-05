from __future__ import annotations

import sys

from passlib.context import CryptContext

schemes = ["argon2", "bcrypt"] if sys.platform.startswith("win") else ["bcrypt"]

pwd_context = CryptContext(schemes=schemes, deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that the given plaintext password matches the hash."""
    return pwd_context.verify(plain_password, hashed_password)


__all__ = ["hash_password", "verify_password"]
