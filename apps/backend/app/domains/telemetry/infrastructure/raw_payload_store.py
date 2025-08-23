from __future__ import annotations

from typing import Optional

from app.domains.telemetry.application.ports.raw_payloads_port import IRawPayloadStore
from app.domains.media.infrastructure.storage.blob_store import put_text


class RawPayloadStore(IRawPayloadStore):
    def put_text(self, prefix: str, data: str, *, filename_hint: Optional[str] = None) -> str:
        return put_text(prefix, data, filename_hint=filename_hint)
