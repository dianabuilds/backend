from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from app.providers.db.session import get_engine
from app.domains.tags.models import Tag
from app.domains.tags.infrastructure.models.tag_models import (
    NodeTag,
    TagAlias,
    TagBlacklist,
    TagMergeLog,
    TagUsageCounter,
)
from app.domains.nodes.models import NodeItem
from app.domains.nodes.infrastructure.models.node import Node
from apps.backendDDD.domains.product.tags.domain.admin_models import (
    AliasView,
    BlacklistItem,
    TagListItem,
)


class SATagsAdminRepo:
    def __init__(self) -> None:
        self._Session = sessionmaker(bind=get_engine().sync_engine, expire_on_commit=False)

    def _uuid(self, v: str) -> uuid.UUID:
        return v if isinstance(v, uuid.UUID) else uuid.UUID(str(v))

    # Listing
    def list_with_counters(self, q: str | None, limit: int, offset: int, content_type: str | None = None) -> List[TagListItem]:
        with self._Session() as s:  # type: Session
            try:
                if content_type:
                    stmt = (
                        sa.select(
                            Tag.id,
                            Tag.slug,
                            Tag.name,
                            Tag.created_at,
                            Tag.is_hidden,
                            sa.func.coalesce(sa.func.sum(TagUsageCounter.count), 0).label("usage_count"),
                            sa.func.count(sa.func.distinct(TagAlias.id)).label("aliases_count"),
                        )
                        .join(TagUsageCounter, Tag.slug == TagUsageCounter.slug, isouter=True)
                        .join(TagAlias, Tag.id == TagAlias.tag_id, isouter=True)
                        .where((TagUsageCounter.content_type == content_type) | (TagUsageCounter.content_type.is_(None)))
                        .group_by(Tag.id)
                    )
                else:
                    stmt = (
                        sa.select(
                            Tag.id,
                            Tag.slug,
                            Tag.name,
                            Tag.created_at,
                            Tag.is_hidden,
                            sa.func.coalesce(sa.func.sum(TagUsageCounter.count), 0).label("usage_count"),
                            sa.func.count(sa.func.distinct(TagAlias.id)).label("aliases_count"),
                        )
                        .join(TagUsageCounter, Tag.slug == TagUsageCounter.slug, isouter=True)
                        .join(TagAlias, Tag.id == TagAlias.tag_id, isouter=True)
                        .group_by(Tag.id)
                    )
                if q:
                    pattern = f"%{q}%"
                    stmt = stmt.where(sa.or_(Tag.slug.ilike(pattern), Tag.name.ilike(pattern)))
                stmt = stmt.order_by(sa.desc("usage_count"), Tag.name).offset(offset).limit(limit)
                rows = s.execute(stmt).all()
                return [
                    TagListItem(
                        id=str(r[0]),
                        slug=r[1],
                        name=r[2],
                        created_at=r[3],
                        is_hidden=bool(r[4]),
                        usage_count=int(r[5] or 0),
                        aliases_count=int(r[6] or 0),
                    )
                    for r in rows
                ]
            except Exception:
                # Projection not available; return tags with zero usage
                stmt = (
                    sa.select(Tag.id, Tag.slug, Tag.name, Tag.created_at, Tag.is_hidden)
                    .order_by(Tag.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
                if q:
                    pattern = f"%{q}%"
                    stmt = stmt.where(sa.or_(Tag.slug.ilike(pattern), Tag.name.ilike(pattern)))
                rows = s.execute(stmt).all()
                return [
                    TagListItem(
                        id=str(r[0]), slug=r[1], name=r[2], created_at=r[3], is_hidden=bool(r[4]), usage_count=0, aliases_count=0
                    )
                    for r in rows
                ]

    def list_aliases(self, tag_id: str) -> List[AliasView]:
        with self._Session() as s:
            res = s.execute(sa.select(TagAlias).where(TagAlias.tag_id == self._uuid(tag_id)).order_by(TagAlias.alias.asc()))
            items = list(res.scalars().all())
            return [
                AliasView(
                    id=str(a.id), tag_id=str(a.tag_id), alias=a.alias, type=a.type, created_at=a.created_at
                )
                for a in items
            ]

    def add_alias(self, tag_id: str, alias: str) -> AliasView:
        with self._Session() as s:
            existing = s.execute(
                sa.select(TagAlias).where(TagAlias.tag_id == self._uuid(tag_id), TagAlias.alias == alias)
            ).scalars().first()
            if existing:
                a = existing
            else:
                a = TagAlias(tag_id=self._uuid(tag_id), alias=alias)
                s.add(a)
                try:
                    s.commit()
                except IntegrityError as e:
                    s.rollback()
                    raise ValueError("alias already exists") from e
            return AliasView(id=str(a.id), tag_id=str(a.tag_id), alias=a.alias, type=a.type, created_at=a.created_at)

    def remove_alias(self, alias_id: str) -> None:
        with self._Session() as s:
            a = s.get(TagAlias, self._uuid(alias_id))
            if a:
                s.delete(a)
                s.commit()

    # Blacklist
    def blacklist_list(self, q: str | None) -> List[BlacklistItem]:
        with self._Session() as s:
            stmt = sa.select(TagBlacklist)
            if q:
                pattern = f"%{q}%"
                stmt = stmt.where(TagBlacklist.slug.ilike(pattern))
            rows = list(s.execute(stmt.order_by(TagBlacklist.created_at.desc())).scalars().all())
            return [BlacklistItem(slug=i.slug, reason=i.reason, created_at=i.created_at) for i in rows]

    def blacklist_add(self, slug: str, reason: str | None) -> BlacklistItem:
        with self._Session() as s:
            existing = s.get(TagBlacklist, slug)
            if existing:
                item = existing
            else:
                item = TagBlacklist(slug=slug, reason=reason)
                s.add(item)
                s.commit()
            return BlacklistItem(slug=item.slug, reason=item.reason, created_at=item.created_at)

    def blacklist_delete(self, slug: str) -> None:
        with self._Session() as s:
            item = s.get(TagBlacklist, slug)
            if item:
                s.delete(item)
                s.commit()

    # CRUD
    def create_tag(self, slug: str, name: str) -> TagListItem:
        with self._Session() as s:
            if s.get(TagBlacklist, slug):
                raise ValueError("slug blacklisted")
            existing = s.execute(sa.select(Tag).where(Tag.slug == slug)).scalar_one_or_none()
            if existing:
                raise ValueError("tag exists")
            tag = Tag(slug=slug, name=name)
            s.add(tag)
            s.commit()
            s.refresh(tag)
            return TagListItem(
                id=str(tag.id),
                slug=tag.slug,
                name=tag.name,
                created_at=tag.created_at,
                is_hidden=bool(tag.is_hidden),
                usage_count=0,
                aliases_count=0,
            )

    def delete_tag(self, tag_id: str) -> None:
        tid = self._uuid(tag_id)
        with self._Session() as s:
            s.execute(sa.delete(TagAlias).where(TagAlias.tag_id == tid))
            s.execute(sa.delete(NodeTag).where(NodeTag.tag_id == tid))
            t = s.get(Tag, tid)
            if t:
                # remove projection counters for this slug
                s.execute(sa.delete(TagUsageCounter).where(TagUsageCounter.slug == t.slug))
                s.delete(t)
            s.commit()

    # Merge
    def merge_dry_run(self, from_id: str, to_id: str, content_type: str | None = None) -> dict:
        if str(from_id) == str(to_id):
            return {"errors": ["from and to tags must be different"], "warnings": []}
        with self._Session() as s:
            from_tag = s.get(Tag, self._uuid(from_id))
            to_tag = s.get(Tag, self._uuid(to_id))
            if not from_tag or not to_tag:
                return {"errors": ["tag not found"], "warnings": []}
            # For node content we can estimate impacted relations via NodeTag
            cnt = 0
            if content_type in (None, "all", "node"):
                cnt = (
                    s.execute(sa.select(sa.func.count(NodeTag.node_id)).where(NodeTag.tag_id == self._uuid(from_id))).scalar()
                    or 0
                )
            # Also report total usage in projection (filtered by type if provided)
            usage_q = sa.select(sa.func.coalesce(sa.func.sum(TagUsageCounter.count), 0)).where(
                TagUsageCounter.slug == from_tag.slug
            )
            if content_type in ("node", "quest"):
                usage_q = usage_q.where(TagUsageCounter.content_type == content_type)
            usage_total = int(s.execute(usage_q).scalar() or 0)
            aliases = s.execute(sa.select(sa.func.count(TagAlias.id)).where(TagAlias.tag_id == self._uuid(from_id))).scalar() or 0
            return {
                "from": {"id": str(from_tag.id), "name": from_tag.name, "slug": from_tag.slug},
                "to": {"id": str(to_tag.id), "name": to_tag.name, "slug": to_tag.slug},
                "content_touched": int(cnt),
                "usage_counters": usage_total,
                "aliases_moved": int(aliases),
                "warnings": [],
                "errors": [],
            }

    def merge_apply(self, from_id: str, to_id: str, actor_id: str | None, reason: str | None, content_type: str | None = None) -> dict:
        report = self.merge_dry_run(from_id, to_id, content_type)
        if report.get("errors"):
            return report
        fid, tid = self._uuid(from_id), self._uuid(to_id)
        with self._Session() as s:
            # For node content type, move NodeTag relations
            if content_type in (None, "all", "node"):
                subq = sa.select(NodeTag.node_id).where(NodeTag.tag_id == fid).scalar_subquery()
                s.execute(sa.delete(NodeTag).where(NodeTag.tag_id == tid, NodeTag.node_id.in_(subq)))
                s.execute(sa.update(NodeTag).where(NodeTag.tag_id == fid).values(tag_id=tid))
            # Move aliases
            for alias in s.execute(sa.select(TagAlias).where(TagAlias.tag_id == fid)).scalars().all():
                alias.tag_id = tid
            # Update projection counters: move slug counts fid->tid
            from_tag = s.get(Tag, fid)
            to_tag = s.get(Tag, tid)
            if from_tag and to_tag:
                q = sa.select(
                    TagUsageCounter.author_id, TagUsageCounter.content_type, TagUsageCounter.count
                ).where(
                    TagUsageCounter.slug == from_tag.slug
                )
                if content_type in ("node", "quest"):
                    q = q.where(TagUsageCounter.content_type == content_type)
                rows = s.execute(q).all()
                for author_id, ctype, value in rows:
                    existing = s.get(TagUsageCounter, (author_id, ctype, to_tag.slug))
                    if existing is None:
                        s.add(TagUsageCounter(author_id=author_id, content_type=ctype, slug=to_tag.slug, count=int(value or 0)))
                    else:
                        existing.count = int(existing.count or 0) + int(value or 0)
                # Delete source counters for selected content_type or all
                del_q = sa.delete(TagUsageCounter).where(TagUsageCounter.slug == from_tag.slug)
                if content_type in ("node", "quest"):
                    del_q = del_q.where(TagUsageCounter.content_type == content_type)
                s.execute(del_q)
            # Remove old tag
            t = s.get(Tag, fid)
            if t:
                s.delete(t)
            # Log merge
            s.add(
                TagMergeLog(
                    from_tag_id=fid,
                    to_tag_id=tid,
                    merged_by=self._uuid(actor_id) if actor_id else None,
                    merged_at=datetime.utcnow(),
                    dry_run=False,
                    reason=reason or None,
                    report=report,
                )
            )
            s.commit()
            return report
