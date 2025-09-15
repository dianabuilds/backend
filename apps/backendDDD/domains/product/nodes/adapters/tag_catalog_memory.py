from __future__ import annotations

from collections.abc import Sequence

from apps.backendDDD.domains.product.nodes.application.ports import TagCatalog


class MemoryTagCatalog(TagCatalog):
    def __init__(
        self,
        *,
        blacklist: set[str] | None = None,
        aliases: dict[str, str] | None = None,
    ) -> None:
        self.blacklist = set(blacklist or set())
        # alias -> slug
        self.aliases = dict(aliases or {})

    def ensure_canonical_slugs(self, slugs: Sequence[str]) -> list[str]:
        out: list[str] = []
        for s in slugs:
            v = (s or "").strip().lower()
            if not v:
                continue
            if v in self.blacklist:
                raise ValueError(f"blacklisted: {v}")
            if v in self.aliases:
                v = self.aliases[v]
            if v not in out:
                out.append(v)
        return out
