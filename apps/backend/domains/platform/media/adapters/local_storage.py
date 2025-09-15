from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path
from typing import BinaryIO


class LocalStorageGateway:
    """Local filesystem storage adapter.

    Saves files under ``apps/apps/backend/var/uploads`` and returns URL path
    ``/v1/media/file/<name>`` which is served by the media API router.
    """

    def __init__(
        self,
        base_dir: str = "apps/backend/var/uploads",
        public_route_prefix: str = "/v1/media/file",
    ) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.public_route_prefix = public_route_prefix

    def save(self, fileobj: BinaryIO, filename: str, content_type: str) -> str:
        ext = mimetypes.guess_extension(content_type) or Path(filename).suffix or ".bin"
        uid = uuid.uuid4().hex
        # Two‑level sharding to avoid too many files in one dir
        shard_a, shard_b = uid[:2], uid[2:4]
        safe_name = f"{uid}{ext.lower()}"
        target_dir = self.base_dir / shard_a / shard_b
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / safe_name
        with open(target, "wb") as f:
            f.write(fileobj.read())
        return f"{self.public_route_prefix}/{shard_a}/{shard_b}/{safe_name}"


__all__ = ["LocalStorageGateway"]
