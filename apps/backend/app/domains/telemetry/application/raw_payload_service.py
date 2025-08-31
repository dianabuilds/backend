from __future__ import annotations

import os

from app.domains.telemetry.application.ports.raw_payloads_port import IRawPayloadStore


class RawPayloadService:
    """
    Сервис для сохранения больших «сырых» текстов:
    - кладёт полный текст во внешнее хранилище с префиксом ai_raw
    - возвращает (url, truncated) — ссылка на полный файл и усечённую копию для БД
    """

    def __init__(
        self, store: IRawPayloadStore, *, max_db_len: int | None = None
    ) -> None:
        self._store = store
        # Максимальная длина копии в БД (символы)
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
