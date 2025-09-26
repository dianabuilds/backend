from __future__ import annotations

import asyncio
import json
from pathlib import Path

from domains.platform.search.ports import Doc, SearchPersistence


class FileSearchPersistence(SearchPersistence):
    def __init__(self, path: str) -> None:
        self._path = Path(path)

    async def load(self) -> list[Doc]:
        p = self._path
        if not p.exists():
            return []
        text = await asyncio.to_thread(p.read_text, encoding="utf-8")
        try:
            arr = json.loads(text)
            out: list[Doc] = []
            for it in arr or []:
                out.append(
                    Doc(
                        id=str(it.get("id")),
                        title=str(it.get("title", "")),
                        text=str(it.get("text", "")),
                        tags=tuple(it.get("tags") or ()),
                    )
                )
            return out
        except Exception:
            return []

    async def save(self, docs: list[Doc]) -> None:
        p = self._path
        # Ensure directory exists
        await asyncio.to_thread(p.parent.mkdir, parents=True, exist_ok=True)
        data = [{"id": d.id, "title": d.title, "text": d.text, "tags": list(d.tags)} for d in docs]
        await asyncio.to_thread(
            p.write_text, json.dumps(data, ensure_ascii=False, indent=2), "utf-8"
        )


__all__ = ["FileSearchPersistence"]
