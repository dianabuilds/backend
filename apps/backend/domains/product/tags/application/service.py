from __future__ import annotations

from domains.product.tags.application.ports import Repo
from domains.product.tags.domain.results import TagView


class TagService:
    def __init__(self, repo: Repo):
        self.repo = repo

    def list_for_user(
        self,
        user_id: str,
        q: str | None,
        popular: bool,
        limit: int,
        offset: int,
        *,
        content_type: str | None = None,
    ) -> list[TagView]:
        # No complex policies yet; delegate to repo with light bounds checks
        limit = max(1, min(int(limit or 10), 200))
        offset = max(0, int(offset or 0))
        if content_type not in (None, "node", "quest", "all"):
            content_type = None
        # Normalize "all" to None at repo layer
        ctype = None if content_type in (None, "all") else content_type
        return self.repo.list_for_user(user_id, q, popular, limit, offset, ctype)
