from __future__ import annotations

from collections.abc import Sequence

from apps.backendDDD.domains.platform.search.ports import Doc, Hit, IndexPort, QueryPort


def _tokens(text: str) -> list[str]:
    import re

    return [t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if t]


class InMemoryIndex(IndexPort, QueryPort):
    def __init__(self) -> None:
        self._docs: dict[str, Doc] = {}
        self._tf: dict[str, dict[str, float]] = {}  # doc_id -> token -> weight
        self._df: dict[str, int] = {}  # token -> doc freq

    async def upsert(self, doc: Doc) -> None:
        # Remove old tokens if replace
        if doc.id in self._tf:
            for tok in self._tf[doc.id].keys():
                self._df[tok] = max(self._df.get(tok, 1) - 1, 0)
        # Tokenize: title has higher weight
        weights: dict[str, float] = {}
        for t in _tokens(doc.title):
            weights[t] = weights.get(t, 0.0) + 2.0
        for t in _tokens(doc.text):
            weights[t] = weights.get(t, 0.0) + 1.0
        # Update doc and stats
        self._docs[doc.id] = doc
        self._tf[doc.id] = weights
        for tok in weights.keys():
            self._df[tok] = self._df.get(tok, 0) + 1

    async def delete(self, id: str) -> None:  # noqa: A002 - id name OK here
        if id in self._docs:
            for tok in self._tf.get(id, {}).keys():
                self._df[tok] = max(self._df.get(tok, 1) - 1, 0)
            self._docs.pop(id, None)
            self._tf.pop(id, None)

    async def list_all(self) -> list[Doc]:
        return list(self._docs.values())

    async def search(
        self, q: str, *, tags: Sequence[str] | None, match: str, limit: int, offset: int
    ) -> list[Hit]:
        tagset = {t.lower() for t in (tags or [])}
        q_tokens = _tokens(q or "")
        results: list[Hit] = []
        N = max(len(self._docs), 1)
        for doc_id, doc in self._docs.items():
            # Tag filter
            if tagset:
                dtag = {t.lower() for t in doc.tags}
                if match == "all":
                    if not tagset.issubset(dtag):
                        continue
                else:
                    if not (tagset & dtag):
                        continue
            # Score by simple TF-IDF
            tf = self._tf.get(doc_id, {})
            score = 0.0
            for qt in q_tokens or []:
                if qt not in tf:
                    continue
                df = max(self._df.get(qt, 1), 1)
                idf = 1.0 + (N / df)
                score += tf[qt] * idf
            if q_tokens and score <= 0.0:
                continue
            # If no query, return by recency/alpha (here uniform score)
            if not q_tokens:
                score = 1.0
            results.append(Hit(id=doc.id, score=score, title=doc.title, tags=doc.tags))
        results.sort(key=lambda h: h.score, reverse=True)
        return results[offset : offset + limit]


__all__ = ["InMemoryIndex"]
