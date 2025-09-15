# AGENT — Search

Где править:
- Индекс: `adapters/memory_index.py` (TF‑IDF/токены/веса)
- Кэш: `adapters/cache_{memory,redis}.py`
- Snapshot: `adapters/persist_file.py`
- API: `api/http.py`
- DI: `wires.py` (кэш и загрузка snapshot)

Правила:
- Любой upsert/delete инвалидирует кэш (version bump) и сохраняет snapshot.
- События `profile.updated.v1` индексируются автоматически (`wires.register_event_indexers`).

