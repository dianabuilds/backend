from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from starlette import status
from starlette.responses import Response

from packages.core.errors import ApiError

SETTINGS_SCHEMA_VERSION = "1.0.0"
SETTINGS_SCHEMA_HEADER = "X-Settings-Schema"


def attach_settings_schema(
    payload: dict[str, Any],
    response: Response,
    *,
    version: str = SETTINGS_SCHEMA_VERSION,
) -> dict[str, Any]:
    """Inject schema metadata into response payload and headers."""
    response.headers[SETTINGS_SCHEMA_HEADER] = version
    if isinstance(payload, dict):
        payload.setdefault("schema_version", version)
    return payload


def set_etag(response: Response, etag: str) -> None:
    response.headers["ETag"] = f'"{etag}"'


def compute_etag(data: Any) -> str:
    if isinstance(data, (bytes, bytearray)):
        raw = bytes(data)
    elif isinstance(data, str):
        raw = data.encode("utf-8")
    else:
        raw = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    return sha256(raw).hexdigest()


def assert_if_match(header_value: str | None, current_etag: str) -> None:
    """Validate If-Match header against the current ETag.

    Accepts strong validators separated by commas or the wildcard `*`.
    """
    if not header_value:
        raise ApiError(
            code="E_ETAG_REQUIRED",
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            message="If-Match header required",
        )
    candidates: list[str] = []
    for token in header_value.split(","):
        token = token.strip()
        if not token:
            continue
        if token == "*":
            return
        if token.startswith('"') and token.endswith('"'):
            token = token[1:-1]
        candidates.append(token)
    if current_etag not in candidates:
        raise ApiError(
            code="E_ETAG_CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            message="Resource version mismatch",
        )


__all__ = [
    "SETTINGS_SCHEMA_VERSION",
    "SETTINGS_SCHEMA_HEADER",
    "attach_settings_schema",
    "set_etag",
    "compute_etag",
    "assert_if_match",
]
