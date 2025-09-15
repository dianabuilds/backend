from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from app.providers.db.session import get_engine
from app.domains.tags.models import Tag
from app.domains.tags.infrastructure.models.tag_models import TagAlias, TagBlacklist


class SATagCatalog:
    """Canonical tag resolver: alias -> slug, create missing, reject blacklisted."""

    def __init__(self) -> None:
        self._Session = sessionmaker(bind=get_engine().sync_engine, expire_on_commit=False)

    def ensure_canonical_slugs(self, slugs: Sequence[str]) -> list[str]:
        out: list[str] = []
        norm = [(s or "").strip().lower() for s in slugs]
        with self._Session() as s:  # type: Session
            # Reject blacklisted
            if norm:
                bl = s.execute(sa.select(TagBlacklist.slug).where(TagBlacklist.slug.in_(norm))).all()
                blocked = {r[0] for r in bl}
                if blocked:
                    raise ValueError(f"blacklisted: {sorted(blocked)}")
            for slug in norm:
                # Alias resolution
                alias = s.execute(sa.select(TagAlias).where(TagAlias.alias == slug)).scalar_one_or_none()
                if alias:
                    # Map to the target tag's slug
                    t = s.get(Tag, alias.tag_id)
                    if t:
                        out.append(t.slug)
                        continue
                # Existing tag?
                t = s.execute(sa.select(Tag).where(Tag.slug == slug)).scalar_one_or_none()
                if t:
                    out.append(t.slug)
                    continue
                # Create new tag (name=slug)
                try:
                    t = Tag(slug=slug, name=slug)
                    s.add(t)
                    s.commit()
                    out.append(t.slug)
                except IntegrityError:
                    s.rollback()
                    # Race: re-fetch
                    t = s.execute(sa.select(Tag).where(Tag.slug == slug)).scalar_one_or_none()
                    if t:
                        out.append(t.slug)
                    else:
                        raise
        return out

