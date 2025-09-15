from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from domains.product.tags.adapters.store_memory import TagUsageStore
from domains.product.tags.application.admin_ports import AdminRepo
from domains.product.tags.domain.admin_models import (
    AliasView,
    BlacklistItem,
    TagListItem,
)


def _uuid() -> str:
    return str(uuid.uuid4())


@dataclass
class _Tag:
    id: str
    slug: str
    name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    is_hidden: bool = False


@dataclass
class _Alias:
    id: str
    tag_id: str
    alias: str
    type: str = "alias"
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


class MemoryAdminRepo(AdminRepo):
    def __init__(self, usage: TagUsageStore | None = None) -> None:
        self._tags: dict[str, _Tag] = {}
        self._by_slug: dict[str, str] = {}
        self._aliases: dict[str, _Alias] = {}
        self._aliases_by_tag: dict[str, list[str]] = {}
        self._blacklist: dict[str, str | None] = {}
        self._usage = usage or TagUsageStore()

    def _usage_count(self, slug: str, content_type: str | None) -> int:
        # Sum counters across all users for given slug
        total = 0
        # access internal store directly
        store = self._usage._cnt  # type: ignore[attr-defined]
        for _aid, by_type in store.items():
            if content_type:
                total += int(by_type.get(content_type, {}).get(slug, 0))
            else:
                for items in by_type.values():
                    total += int(items.get(slug, 0))
        return int(total)

    def list_with_counters(
        self, q: str | None, limit: int, offset: int, content_type: str | None = None
    ) -> list[TagListItem]:
        items = list(self._tags.values())
        if q:
            ql = q.lower()
            items = [
                t for t in items if ql in t.slug.lower() or ql in (t.name or "").lower()
            ]
        items.sort(key=lambda t: t.name or t.slug)
        items = items[offset : offset + limit]
        out: list[TagListItem] = []
        for t in items:
            aliases_count = len(self._aliases_by_tag.get(t.id, []))
            usage_count = self._usage_count(t.slug, content_type)
            out.append(
                TagListItem(
                    id=t.id,
                    slug=t.slug,
                    name=t.name,
                    created_at=t.created_at,
                    is_hidden=bool(t.is_hidden),
                    usage_count=int(usage_count),
                    aliases_count=int(aliases_count),
                )
            )
        return out

    def list_aliases(self, tag_id: str) -> list[AliasView]:
        ids = self._aliases_by_tag.get(str(tag_id), [])
        out: list[AliasView] = []
        for aid in ids:
            a = self._aliases[aid]
            out.append(
                AliasView(
                    id=a.id,
                    tag_id=a.tag_id,
                    alias=a.alias,
                    type=a.type,
                    created_at=a.created_at,
                )
            )
        return out

    def add_alias(self, tag_id: str, alias: str) -> AliasView:
        if str(tag_id) not in self._tags:
            raise ValueError("tag_not_found")
        if alias in self._by_slug:
            raise ValueError("alias_conflict")
        a = _Alias(id=_uuid(), tag_id=str(tag_id), alias=str(alias))
        self._aliases[a.id] = a
        self._aliases_by_tag.setdefault(a.tag_id, []).append(a.id)
        return AliasView(
            id=a.id,
            tag_id=a.tag_id,
            alias=a.alias,
            type=a.type,
            created_at=a.created_at,
        )

    def remove_alias(self, alias_id: str) -> None:
        a = self._aliases.pop(str(alias_id), None)
        if not a:
            return
        lst = self._aliases_by_tag.get(a.tag_id)
        if lst and alias_id in lst:
            lst.remove(alias_id)

    def blacklist_list(self, q: str | None) -> list[BlacklistItem]:
        items = list(self._blacklist.items())
        if q:
            ql = q.lower()
            items = [(k, v) for (k, v) in items if ql in k.lower()]
        return [
            BlacklistItem(slug=k, reason=v, created_at=datetime.now(tz=UTC))
            for (k, v) in items
        ]

    def blacklist_add(self, slug: str, reason: str | None) -> BlacklistItem:
        self._blacklist[str(slug)] = reason
        return BlacklistItem(
            slug=str(slug), reason=reason, created_at=datetime.now(tz=UTC)
        )

    def blacklist_delete(self, slug: str) -> None:
        self._blacklist.pop(str(slug), None)

    def create_tag(self, slug: str, name: str) -> TagListItem:
        if slug in self._by_slug:
            raise ValueError("conflict")
        tid = _uuid()
        t = _Tag(id=tid, slug=str(slug), name=str(name))
        self._tags[tid] = t
        self._by_slug[t.slug] = tid
        return TagListItem(
            id=tid,
            slug=t.slug,
            name=t.name,
            created_at=t.created_at,
            is_hidden=False,
            usage_count=int(self._usage_count(t.slug, None)),
            aliases_count=0,
        )

    def delete_tag(self, tag_id: str) -> None:
        t = self._tags.pop(str(tag_id), None)
        if not t:
            return
        self._by_slug.pop(t.slug, None)
        # remove aliases
        for aid in self._aliases_by_tag.get(t.id, []):
            self._aliases.pop(aid, None)
        self._aliases_by_tag.pop(t.id, None)
        # drop usage counters for slug
        store = self._usage._cnt  # type: ignore[attr-defined]
        for by_type in store.values():
            for ctype in list(by_type.keys()):
                by_type[ctype].pop(t.slug, None)

    def merge_dry_run(
        self, from_id: str, to_id: str, content_type: str | None = None
    ) -> dict:
        f = self._tags.get(str(from_id))
        t = self._tags.get(str(to_id))
        if not f or not t:
            return {"errors": ["tag not found"], "warnings": []}
        usage = self._usage_count(f.slug, content_type)
        aliases = len(self._aliases_by_tag.get(str(from_id), []))
        return {
            "from": {"id": f.id, "name": f.name, "slug": f.slug},
            "to": {"id": t.id, "name": t.name, "slug": t.slug},
            "content_touched": 0,
            "usage_counters": int(usage),
            "aliases_moved": int(aliases),
            "warnings": [],
            "errors": [],
        }

    def merge_apply(
        self,
        from_id: str,
        to_id: str,
        actor_id: str | None,
        reason: str | None,
        content_type: str | None = None,
    ) -> dict:
        report = self.merge_dry_run(from_id, to_id, content_type)
        if report.get("errors"):
            return report
        f = self._tags.get(str(from_id))
        t = self._tags.get(str(to_id))
        if not f or not t:
            return report
        # Move usage counters from f.slug to t.slug
        store = self._usage._cnt  # type: ignore[attr-defined]
        for _aid, by_type in store.items():
            if content_type:
                cnt = int(by_type.get(content_type, {}).get(f.slug, 0))
                if cnt:
                    by_type.setdefault(content_type, {})
                    by_type[content_type][t.slug] = (
                        int(by_type[content_type].get(t.slug, 0)) + cnt
                    )
                    by_type[content_type].pop(f.slug, None)
            else:
                for _ctype, items in by_type.items():
                    cnt = int(items.get(f.slug, 0))
                    if cnt:
                        items[t.slug] = int(items.get(t.slug, 0)) + cnt
                        items.pop(f.slug, None)
        # Move aliases
        for aid in list(self._aliases_by_tag.get(f.id, [])):
            a = self._aliases[aid]
            a.tag_id = t.id
            self._aliases_by_tag.setdefault(t.id, []).append(aid)
        self._aliases_by_tag.pop(f.id, None)
        # Delete old tag
        self.delete_tag(f.id)
        return report
