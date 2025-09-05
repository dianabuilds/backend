from __future__ import annotations

from app.domains.media.infrastructure.storage.blob_store import put_text
from app.domains.telemetry.application.ports.raw_payloads_port import IRawPayloadStore


class RawPayloadStore(IRawPayloadStore):
    def put_text(self, prefix: str, data: str, *, filename_hint: str | None = None) -> str:
        return put_text(prefix, data, filename_hint=filename_hint)
