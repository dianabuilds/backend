from __future__ import annotations

import uuid

from sqlalchemy.orm import Session, sessionmaker

from app.providers.db.session import get_engine
from app.domains.tags.infrastructure.models.tag_models import TagUsageCounter


class SATagUsageProjection:
    def __init__(self) -> None:
        self._Session = sessionmaker(bind=get_engine().sync_engine, expire_on_commit=False)

    def _uuid(self, v: str) -> uuid.UUID:
        return v if isinstance(v, uuid.UUID) else uuid.UUID(str(v))

    def apply_diff(self, author_id: str, added: list[str], removed: list[str], *, content_type: str = "node") -> None:
        aid = self._uuid(author_id)
        with self._Session() as s:  # type: Session
            # Increment for added
            for slug in added:
                row = s.get(TagUsageCounter, (aid, content_type, slug))
                if row is None:
                    row = TagUsageCounter(author_id=aid, content_type=content_type, slug=slug, count=1)
                    s.add(row)
                else:
                    row.count = int(row.count or 0) + 1
            # Decrement for removed
            for slug in removed:
                row = s.get(TagUsageCounter, (aid, content_type, slug))
                if row is None:
                    continue
                c = int(row.count or 0) - 1
                if c <= 0:
                    s.delete(row)
                else:
                    row.count = c
            s.commit()
