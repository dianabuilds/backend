from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from domains.platform.search.ports import Doc, SearchPersistence

logger = logging.getLogger(__name__)


class FileSearchPersistence(SearchPersistence):
    def __init__(self, path: str) -> None:
        self._path = Path(path)

    async def load(self) -> list[Doc]:
        p = self._path
        if not p.exists():
            return []
        try:
            text = await asyncio.to_thread(p.read_text, encoding="utf-8")
        except OSError as exc:
            logger.warning("search persistence: failed reading %s: %s", p, exc)
            return []
        try:
            arr = json.loads(text)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("search persistence: invalid JSON payload in %s: %s", p, exc)
            return []
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

    async def save(self, docs: list[Doc]) -> None:
        p = self._path
        data = [
            {"id": d.id, "title": d.title, "text": d.text, "tags": list(d.tags)}
            for d in docs
        ]
        try:
            await asyncio.to_thread(p.parent.mkdir, parents=True, exist_ok=True)
            await asyncio.to_thread(
                p.write_text, json.dumps(data, ensure_ascii=False, indent=2), "utf-8"
            )
        except OSError as exc:
            logger.error("search persistence: failed writing %s: %s", p, exc)


__all__ = ["FileSearchPersistence"]
