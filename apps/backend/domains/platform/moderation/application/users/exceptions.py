from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ModerationUserError(Exception):
    code: str
    status_code: int = 400
    message: str | None = None

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message or self.code)


class UserNotFoundError(ModerationUserError):
    def __init__(self, code: str = "user_not_found", status_code: int = 404) -> None:
        super().__init__(code=code, status_code=status_code)


__all__ = [
    "ModerationUserError",
    "UserNotFoundError",
]
