from __future__ import annotations

import re

from domains.platform.events.ports import OutboxPublisher
from domains.product.tags.application.admin_ports import AdminRepo


def _norm_slug(s: str) -> str:
    return (s or "").strip().lower()


def _norm_name(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _norm_alias(s: str) -> str:
    return _norm_name(s).lower()


class TagAdminService:
    def __init__(self, repo: AdminRepo, outbox: OutboxPublisher | None = None):
        self.repo = repo
        self.outbox = outbox

    # Queries
    def list_tags(
        self, q: str | None, limit: int, offset: int, *, content_type: str | None = None
    ):
        limit = max(1, min(int(limit or 50), 1000))
        offset = max(0, int(offset or 0))
        if content_type not in (None, "node", "quest", "all"):
            content_type = None
        ctype = None if content_type in (None, "all") else content_type
        return self.repo.list_with_counters(q, limit, offset, ctype)

    def list_aliases(self, tag_id: str):
        return self.repo.list_aliases(tag_id)

    # Mutations
    def add_alias(self, tag_id: str, alias: str):
        res = self.repo.add_alias(tag_id, _norm_alias(alias))
        try:
            if self.outbox:
                self.outbox.publish(
                    "tag.alias.added.v1", {"tag_id": tag_id, "alias": res.alias}
                )
        except Exception:
            pass
        return res

    def remove_alias(self, alias_id: str) -> None:
        self.repo.remove_alias(alias_id)
        try:
            if self.outbox:
                self.outbox.publish("tag.alias.removed.v1", {"alias_id": alias_id})
        except Exception:
            pass

    def blacklist_list(self, q: str | None):
        return self.repo.blacklist_list(q)

    def blacklist_add(self, slug: str, reason: str | None):
        res = self.repo.blacklist_add(_norm_slug(slug), reason)
        try:
            if self.outbox:
                self.outbox.publish(
                    "tag.blacklist.added.v1", {"slug": res.slug, "reason": res.reason}
                )
        except Exception:
            pass
        return res

    def blacklist_delete(self, slug: str) -> None:
        self.repo.blacklist_delete(_norm_slug(slug))
        try:
            if self.outbox:
                self.outbox.publish(
                    "tag.blacklist.removed.v1", {"slug": _norm_slug(slug)}
                )
        except Exception:
            pass

    def create_tag(self, slug: str, name: str):
        res = self.repo.create_tag(_norm_slug(slug), _norm_name(name))
        try:
            if self.outbox:
                self.outbox.publish(
                    "tag.created.v1", {"id": res.id, "slug": res.slug, "name": res.name}
                )
        except Exception:
            pass
        return res

    def delete_tag(self, tag_id: str) -> None:
        self.repo.delete_tag(tag_id)
        try:
            if self.outbox:
                self.outbox.publish("tag.deleted.v1", {"id": tag_id})
        except Exception:
            pass

    def merge_dry_run(
        self, from_id: str, to_id: str, *, content_type: str | None = None
    ) -> dict:
        return self.repo.merge_dry_run(from_id, to_id, content_type)

    def merge_apply(
        self,
        from_id: str,
        to_id: str,
        actor_id: str | None,
        reason: str | None,
        *,
        content_type: str | None = None,
    ) -> dict:
        report = self.repo.merge_apply(from_id, to_id, actor_id, reason, content_type)
        try:
            if self.outbox:
                self.outbox.publish(
                    "tag.merged.v1",
                    {
                        "from_id": from_id,
                        "to_id": to_id,
                        "actor_id": actor_id,
                        "reason": reason,
                        "content_type": content_type,
                    },
                )
        except Exception:
            pass
        return report
