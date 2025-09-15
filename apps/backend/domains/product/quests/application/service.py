from __future__ import annotations

import hashlib
import time
from collections.abc import Sequence

from domains.product.quests.application.ports import (
    CreateQuestInput,
    Outbox,
    Repo,
    TagCatalog,
)
from domains.product.quests.domain.results import QuestView
from packages.core import with_trace


class QuestService:
    def __init__(self, repo: Repo, tags: TagCatalog, outbox: Outbox):
        self.repo, self.tags, self.outbox = repo, tags, outbox

    def get(self, quest_id: str) -> QuestView | None:
        q = self.repo.get(quest_id)
        if not q:
            return None
        return QuestView(
            id=q.id,
            author_id=q.author_id,
            slug=q.slug,
            title=q.title,
            description=q.description,
            tags=list(q.tags),
            is_public=q.is_public,
        )

    @with_trace
    def create(self, data: CreateQuestInput) -> QuestView:
        # simple slug: could be replaced by a slugger
        slug = hashlib.sha256(
            f"{data.author_id}-{data.title}-{time.time()}".encode()
        ).hexdigest()[:16]
        tags = self.tags.ensure_canonical_slugs(list(data.tags or ()))
        created = self.repo.create(
            CreateQuestInput(
                author_id=data.author_id,
                title=data.title,
                description=data.description,
                tags=tags,
                is_public=bool(data.is_public),
            ),
            slug=slug,
        )
        try:
            self.outbox.publish(
                "quest.created.v1",
                {
                    "id": created.id,
                    "author_id": created.author_id,
                    "slug": created.slug,
                    "title": created.title,
                },
                key=f"quest:{created.id}",
            )
            if tags:
                self.outbox.publish(
                    "quest.tags.updated.v1",
                    {
                        "id": created.id,
                        "author_id": created.author_id,
                        "added": list(tags),
                        "removed": [],
                        "content_type": "quest",
                    },
                    key=f"quest:{created.id}:tags",
                )
        except Exception:
            pass
        return self.get(created.id) or QuestView(
            id=created.id,
            author_id=created.author_id,
            slug=created.slug,
            title=created.title,
            description=created.description,
            tags=list(created.tags),
            is_public=created.is_public,
        )

    @with_trace
    def update_tags(
        self, quest_id: str, new_slugs: Sequence[str], *, actor_id: str
    ) -> QuestView:
        tags = self.tags.ensure_canonical_slugs(list(new_slugs))
        before = self.repo.get(quest_id)
        updated = self.repo.set_tags(quest_id, tags)
        old = set(before.tags) if before else set()
        new = set(tags)
        added = sorted(new - old)
        removed = sorted(old - new)
        try:
            if added or removed:
                self.outbox.publish(
                    "quest.tags.updated.v1",
                    {
                        "id": updated.id,
                        "author_id": updated.author_id,
                        "added": added,
                        "removed": removed,
                        "content_type": "quest",
                        "actor_id": actor_id,
                    },
                    key=f"quest:{updated.id}:tags",
                )
        except Exception:
            pass
        return self.get(quest_id) or QuestView(
            id=updated.id,
            author_id=updated.author_id,
            slug=updated.slug,
            title=updated.title,
            description=updated.description,
            tags=list(updated.tags),
            is_public=updated.is_public,
        )
