from __future__ import annotations

import uuid
from typing import List

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app.providers.db.session import get_engine
from app.domains.tags.models import Tag
from app.domains.tags.infrastructure.models.tag_models import TagUsageCounter
from apps.backendDDD.domains.product.tags.domain.results import TagView


class SATagsRepo:
    """Read-only Tags repo for current user based on monolith schema (sync)."""

    def __init__(self) -> None:
        self._Session = sessionmaker(bind=get_engine().sync_engine, expire_on_commit=False)

    def _to_uuid(self, id_str: str) -> uuid.UUID:
        return id_str if isinstance(id_str, uuid.UUID) else uuid.UUID(str(id_str))

    def list_for_user(
        self,
        user_id: str,
        q: str | None,
        popular: bool,
        limit: int,
        offset: int,
        content_type: str | None = None,
    ) -> List[TagView]:
        uid = self._to_uuid(user_id)
        with self._Session() as s:  # type: Session
            try:
                agg = sa.func.coalesce(sa.func.sum(TagUsageCounter.count), 0)
                if content_type:
                    stmt = (
                        sa.select(TagUsageCounter.slug, Tag.name, sa.func.coalesce(sa.func.sum(TagUsageCounter.count), 0))
                        .join(Tag, Tag.slug == TagUsageCounter.slug, isouter=True)
                        .where(TagUsageCounter.author_id == uid, TagUsageCounter.content_type == content_type)
                        .group_by(TagUsageCounter.slug, Tag.name)
                    )
                else:
                    # all types: sum across content types
                    stmt = (
                        sa.select(TagUsageCounter.slug, Tag.name, sa.func.coalesce(sa.func.sum(TagUsageCounter.count), 0))
                        .join(Tag, Tag.slug == TagUsageCounter.slug, isouter=True)
                        .where(TagUsageCounter.author_id == uid)
                        .group_by(TagUsageCounter.slug, Tag.name)
                    )
                if q:
                    pattern = f"%{q}%"
                    stmt = stmt.where(sa.or_(TagUsageCounter.slug.ilike(pattern), (Tag.name.ilike(pattern))))
                stmt = stmt.order_by(agg.desc() if popular else Tag.name.asc())
                stmt = stmt.offset(offset).limit(limit)
                rows = s.execute(stmt).all()
                return [TagView(slug=r[0], name=(r[1] or r[0]), count=int(r[2] or 0)) for r in rows]
            except Exception:
                # Projection missing or schema not migrated yet
                return []

