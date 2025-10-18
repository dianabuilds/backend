from __future__ import annotations

import logging
import re
from typing import Any

from domains.platform.events.application.publisher import OutboxError, OutboxPublisher
from domains.product.tags.application.admin_ports import AdminRepo
from domains.product.tags.domain.admin_models import TagGroupSummary

logger = logging.getLogger(__name__)

try:
    from redis.exceptions import RedisError  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    RedisError = Exception  # type: ignore[misc, assignment]


_OUTBOX_EXPECTED_ERRORS = (ValueError, RuntimeError, RedisError)


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

    def _publish(self, event: str, payload: dict[str, Any]) -> None:
        if not self.outbox:
            return
        extra = {
            "topic": event,
            "tag_id": payload.get("tag_id"),
            "alias_id": payload.get("alias_id"),
            "slug": payload.get("slug"),
        }
        try:
            self.outbox.publish(event, payload)
        except _OUTBOX_EXPECTED_ERRORS as exc:
            logger.warning("tag_admin_outbox_publish_failed", extra=extra, exc_info=exc)
        except Exception as exc:  # pragma: no cover - unexpected failure
            logger.exception(
                "tag_admin_outbox_publish_unexpected", extra=extra, exc_info=exc
            )
            raise OutboxError(
                "tag_admin_outbox_publish_unexpected", topic=event
            ) from exc

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

    def list_groups(self) -> list[TagGroupSummary]:
        return self.repo.list_groups()

    def list_aliases(self, tag_id: str):
        return self.repo.list_aliases(tag_id)

    # Mutations
    def add_alias(self, tag_id: str, alias: str):
        res = self.repo.add_alias(tag_id, _norm_alias(alias))
        self._publish("tag.alias.added.v1", {"tag_id": tag_id, "alias": res.alias})
        return res

    def remove_alias(self, alias_id: str) -> None:
        self.repo.remove_alias(alias_id)
        self._publish("tag.alias.removed.v1", {"alias_id": alias_id})

    def blacklist_list(self, q: str | None):
        return self.repo.blacklist_list(q)

    def blacklist_add(self, slug: str, reason: str | None):
        res = self.repo.blacklist_add(_norm_slug(slug), reason)
        self._publish(
            "tag.blacklist.added.v1", {"slug": res.slug, "reason": res.reason}
        )
        return res

    def blacklist_delete(self, slug: str) -> None:
        self.repo.blacklist_delete(_norm_slug(slug))
        self._publish("tag.blacklist.removed.v1", {"slug": _norm_slug(slug)})

    def create_tag(self, slug: str, name: str):
        res = self.repo.create_tag(_norm_slug(slug), _norm_name(name))
        self._publish(
            "tag.created.v1", {"id": res.id, "slug": res.slug, "name": res.name}
        )
        return res

    def delete_tag(self, tag_id: str) -> None:
        self.repo.delete_tag(tag_id)
        self._publish("tag.deleted.v1", {"id": tag_id})

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
        self._publish(
            "tag.merged.v1",
            {
                "from_id": from_id,
                "to_id": to_id,
                "actor_id": actor_id,
                "reason": reason,
                "content_type": content_type,
            },
        )
        return report


__all__ = ["TagAdminService"]
