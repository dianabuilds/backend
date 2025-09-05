from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path
from typing import BinaryIO


class LocalStorageGateway:
    """Simple local filesystem storage adapter.

    Saves files under uploads/ and returns public URL /static/uploads/<name>.
    """

    def __init__(self, base_dir: str = "uploads", public_prefix: str = "/static/uploads") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.public_prefix = public_prefix

    def save(self, fileobj: BinaryIO, filename: str, content_type: str) -> str:
        """Persist ``fileobj`` and return a public URL."""
        ext = mimetypes.guess_extension(content_type) or Path(filename).suffix or ".bin"
        safe_name = f"{uuid.uuid4().hex}{ext.lower()}"
        target = self.base_dir / safe_name
        with open(target, "wb") as f:
            f.write(fileobj.read())
        return f"{self.public_prefix}/{safe_name}"
