from __future__ import annotations

from collections.abc import Mapping


class ProfileError(Exception):
    def __init__(
        self,
        *,
        code: str,
        status_code: int,
        message: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self.code = code
        self.status_code = status_code
        self.message = message or code
        self.headers = dict(headers or {})
        super().__init__(self.message)


def value_error_to_profile_error(
    error: ValueError,
    *,
    fallback_status: int = 400,
    not_found_codes: frozenset[str] | None = None,
) -> ProfileError:
    code = str(error) or "profile_error"
    if not_found_codes and code in not_found_codes:
        return ProfileError(code=code, status_code=404)
    return ProfileError(code=code, status_code=fallback_status)


__all__ = ["ProfileError", "value_error_to_profile_error"]
