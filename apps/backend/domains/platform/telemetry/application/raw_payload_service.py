from __future__ import annotations

import os

from domains.platform.telemetry.ports.raw_payloads_port import (
    IRawPayloadStore,
)


class RawPayloadService:
    def __init__(
        self, store: IRawPayloadStore, *, max_db_len: int | None = None
    ) -> None:
        self._store = store
        self._max_db_len = (
            int(os.getenv("RAW_LOG_MAX_DB", "16384"))
            if max_db_len is None
            else int(max_db_len)
        )

    def store_large_text(
        self, raw_text: str, *, filename_hint: str = "raw"
    ) -> tuple[str, str]:
        url = self._store.put_text("ai_raw", raw_text, filename_hint=filename_hint)
        if len(raw_text) > self._max_db_len:
            truncated = (
                raw_text[: self._max_db_len] + f"\n\n...[truncated, full: {url}]"
            )
        else:
            truncated = raw_text
        return url, truncated


__all__ = ["RawPayloadService"]
