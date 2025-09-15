from __future__ import annotations

import pytest

from domains.platform.search.adapters.memory_index import InMemoryIndex
from domains.platform.search.adapters.persist_file import (
    FileSearchPersistence,
)
from domains.platform.search.ports import Doc


@pytest.mark.asyncio
async def test_file_persistence_roundtrip(tmp_path):
    p = tmp_path / "search.json"
    persist = FileSearchPersistence(str(p))
    docs = [
        Doc(id="a", title="Alpha", text="first"),
        Doc(id="b", title="Beta", text="second"),
    ]
    await persist.save(docs)

    loaded = await persist.load()
    ids = sorted(d.id for d in loaded)
    assert ids == ["a", "b"]

    # Load into index and confirm searchable
    idx = InMemoryIndex()
    for d in loaded:
        await idx.upsert(d)
    hits = await idx.search("alpha", tags=None, match="any", limit=10, offset=0)
    assert hits and hits[0].id == "a"
